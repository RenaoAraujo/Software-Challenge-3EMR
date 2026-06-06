#!/usr/bin/env python3
"""serial_gateway.py — Ponte serial bidirecional ESP32-P4 ↔ Backend EMR

Ao executar sem argumentos entra em modo interativo:
  - Lista os separadores cadastrados no EMR
  - Lista as portas seriais disponíveis
  - O utilizador escolhe e o gateway inicia

Uso rápido (modo direto):
  python serial_gateway.py --port COM3 --robot-code ESP32-P4-001

Argumentos completos: python serial_gateway.py --help
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any

import requests
import serial
import serial.tools.list_ports

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
BRIDGE_PREFIX  = "BRIDGE:"
CMD_PREFIX     = "CMD:"
CSRF_TTL_S     = 800
RETRY_DELAY_S  = 3
HTTP_TIMEOUT   = 12
POLL_INTERVAL  = 2.0
CONFIG_FILE    = Path(__file__).with_name("gateway_config.json")

STATUS_LABEL = {
    "offline":     "offline",
    "idle":        "disponível",
    "running":     "em execução",
    "paused":      "pausado",
    "error":       "erro",
    "maintenance": "manutenção",
}

# ---------------------------------------------------------------------------
# Logging (nível INFO por padrão; --debug sobe para DEBUG)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("gateway")


# ---------------------------------------------------------------------------
# Cliente HTTP para o backend EMR
# ---------------------------------------------------------------------------
class EMRClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._session = requests.Session()
        self._csrf: str | None = None
        self._csrf_at: float = 0.0

    def login(self) -> None:
        csrf = self._refresh_csrf()
        r = self._session.post(
            f"{self.base}/api/auth/login",
            json={"username": self.username, "password": self.password},
            headers={"X-CSRF-Token": csrf},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()

    def _refresh_csrf(self) -> str:
        r = self._session.get(f"{self.base}/api/csrf-token", timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        self._csrf = r.json()["csrf_token"]
        self._csrf_at = time.monotonic()
        return self._csrf

    def _csrf_token(self) -> str:
        if self._csrf is None or (time.monotonic() - self._csrf_at) > CSRF_TTL_S:
            return self._refresh_csrf()
        return self._csrf

    def _get(self, path: str) -> Any:
        r = self._session.get(f"{self.base}/api{path}", timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict | None = None) -> Any:
        r = self._session.post(
            f"{self.base}/api{path}",
            json=body or {},
            headers={"X-CSRF-Token": self._csrf_token()},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {}

    def _patch(self, path: str, body: dict) -> Any:
        r = self._session.patch(
            f"{self.base}/api{path}",
            json=body,
            headers={"X-CSRF-Token": self._csrf_token()},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()

    def list_robots(self) -> list[dict]:
        return self._get("/robots")  # type: ignore[return-value]

    def find_robot_by_code(self, code: str) -> dict | None:
        for r in self.list_robots():
            if r.get("code") == code:
                return r
        return None

    def get_robot(self, robot_id: int) -> dict:
        return self._get(f"/robots/{robot_id}")  # type: ignore[return-value]

    def ensure_robot_idle(self, robot_id: int) -> None:
        robot = self.get_robot(robot_id)
        if robot.get("status") in ("offline", "maintenance", "error"):
            log.info("Robô %d estava '%s' — alterando para 'idle'", robot_id, robot["status"])
            self._patch(f"/robots/{robot_id}", {"status": "idle"})

    def create_os_and_assign(self, robot_id: int, os_code: str, client_name: str, total: int) -> None:
        body: dict[str, Any] = {
            "os_code": os_code,
            "client_name": client_name,
            "robot_id": robot_id,
            "quantidade_remedios": total,
        }
        try:
            self._post("/service-orders/manual", body)
            log.info("OS '%s' criada e atribuída ao robô %d", os_code, robot_id)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 409:
                log.warning("OS '%s' já existia cancelada — reabrindo com 'restart'", os_code)
                body["reopen_cancelled"] = "restart"
                self._post("/service-orders/manual", body)
                log.info("OS '%s' reaberta (restart) no robô %d", os_code, robot_id)
            else:
                raise

    def update_units(self, robot_id: int, units: int) -> None:
        self._patch(f"/robots/{robot_id}/units", {"units_separated": units})
        log.info("Progresso: %d unidades separadas (robô %d)", units, robot_id)

    def complete_os(self, robot_id: int) -> None:
        try:
            self._post(f"/robots/{robot_id}/concluir-os")
            log.info("OS concluída no robô %d", robot_id)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 400:
                log.info("OS já concluída automaticamente no robô %d (ignorado)", robot_id)
            else:
                raise

    def cancel_os(self, robot_id: int, reason: str) -> None:
        self._post(
            f"/robots/{robot_id}/cancelar-os",
            {"reason_code": "OUTROS", "detail": reason.strip() or "Cancelado pelo separador"},
        )
        log.info("OS cancelada no robô %d — motivo: %s", robot_id, reason)

    def get_last_closed_order(self, os_code: str) -> dict | None:
        try:
            data = self._get(f"/service-orders/completed?os={os_code}&limit=1")
            items = data.get("items", [])
            return items[0] if items else None
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Escrita thread-safe na porta serial
# ---------------------------------------------------------------------------
class SerialWriter:
    def __init__(self) -> None:
        self._port: serial.Serial | None = None
        self._lock = threading.Lock()

    def attach(self, port: serial.Serial) -> None:
        with self._lock:
            self._port = port

    def detach(self) -> None:
        with self._lock:
            self._port = None

    def send_cmd(self, cmd: dict) -> bool:
        line = CMD_PREFIX + json.dumps(cmd, ensure_ascii=False) + "\n"
        with self._lock:
            if self._port is None or not self._port.is_open:
                return False
            try:
                self._port.write(line.encode("utf-8"))
                log.info("[CMD TX] %s", line.strip())
                return True
            except serial.SerialException as exc:
                log.error("Erro ao escrever na serial: %s", exc)
                return False


# ---------------------------------------------------------------------------
# Processador de eventos BRIDGE (ESP32 → Web)
# ---------------------------------------------------------------------------
class EventProcessor:
    def __init__(self, client: EMRClient, robot_id: int) -> None:
        self._client = client
        self._robot_id = robot_id

    def handle(self, ev: dict) -> None:
        event  = ev.get("ev", "")
        os_num = ev.get("num", "?")
        rid    = self._robot_id

        if event == "os_start":
            client_name = ev.get("client", "")
            total = int(ev.get("total", 1))
            log.info("[BRIDGE os_start] OS=%s  cliente='%s'  total=%d", os_num, client_name, total)
            self._client.ensure_robot_idle(rid)
            self._client.create_os_and_assign(rid, os_num, client_name, total)

        elif event == "unit":
            done = int(ev.get("done", 0))
            log.info("[BRIDGE unit]     OS=%s  done=%d", os_num, done)
            self._client.update_units(rid, done)

        elif event == "os_complete":
            done = int(ev.get("done", 0))
            log.info("[BRIDGE os_complete] OS=%s  done=%d", os_num, done)
            self._client.update_units(rid, done)
            self._client.complete_os(rid)

        elif event == "os_cancel":
            done   = int(ev.get("done", 0))
            reason = str(ev.get("reason", ""))
            log.info("[BRIDGE os_cancel]  OS=%s  done=%d  reason='%s'", os_num, done, reason)
            self._client.update_units(rid, done)
            self._client.cancel_os(rid, reason)

        else:
            log.debug("Evento desconhecido ignorado: %s", event)


# ---------------------------------------------------------------------------
# Poller EMR → ESP32
# ---------------------------------------------------------------------------
class EMRPoller:
    def __init__(self, client: EMRClient, writer: SerialWriter, robot_id: int) -> None:
        self._client   = client
        self._writer   = writer
        self._robot_id = robot_id
        self._prev_os_code: str | None = None
        self._prev_units:   int        = 0

    def _fetch(self) -> dict | None:
        try:
            return self._client.get_robot(self._robot_id)
        except Exception as exc:
            log.debug("Poller: erro ao buscar robô: %s", exc)
            return None

    def tick(self) -> None:
        robot = self._fetch()
        if robot is None:
            return

        order         = robot.get("current_order")
        curr_os_code  = order.get("os_code") if order else None
        curr_units    = int(robot.get("units_separated", 0))

        if curr_os_code and curr_os_code != self._prev_os_code:
            total       = int(order.get("expected_units", 1)) if order else 1
            client_name = order.get("client_name", "")        if order else ""
            log.info("[POLLER] Nova OS pelo painel: %s (%d unidades)", curr_os_code, total)
            self._writer.send_cmd({"cmd": "os_assign", "num": curr_os_code,
                                   "client": client_name, "total": total})

        elif self._prev_os_code and not curr_os_code:
            closed  = self._client.get_last_closed_order(self._prev_os_code)
            situacao = closed.get("situacao") if closed else None
            if situacao == "concluida":
                log.info("[POLLER] OS %s concluída pelo painel", self._prev_os_code)
                self._writer.send_cmd({"cmd": "os_complete", "num": self._prev_os_code,
                                       "done": self._prev_units})
            else:
                motivo = (closed.get("erro_descricao") or "Cancelado pelo painel web") if closed else "Cancelado pelo painel web"
                log.info("[POLLER] OS %s cancelada pelo painel — %s", self._prev_os_code, motivo)
                self._writer.send_cmd({"cmd": "os_cancel", "num": self._prev_os_code,
                                       "done": self._prev_units, "reason": motivo})

        self._prev_os_code = curr_os_code
        self._prev_units   = curr_units

    def run(self) -> None:
        log.info("Poller EMR iniciado (intervalo: %.1fs)", POLL_INTERVAL)
        while True:
            try:
                self.tick()
            except Exception as exc:
                log.error("Poller: exceção: %s", exc, exc_info=True)
            time.sleep(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Loop serial
# ---------------------------------------------------------------------------
def run_serial_loop(
    port: str,
    baud: int,
    processor: EventProcessor,
    writer: SerialWriter,
    poller: EMRPoller,
) -> None:
    log.info("Abrindo porta serial %s @ %d baud…", port, baud)
    poll_started = False
    while True:
        try:
            with serial.Serial(port, baud, timeout=1) as ser:
                log.info("Porta %s aberta. Aguardando eventos do ESP32…", port)
                writer.attach(ser)

                if not poll_started:
                    threading.Thread(target=poller.run, daemon=True, name="emr_poller").start()
                    poll_started = True

                while True:
                    raw = ser.readline()
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="replace").strip()
                    if BRIDGE_PREFIX not in line:
                        continue

                    idx      = line.index(BRIDGE_PREFIX) + len(BRIDGE_PREFIX)
                    json_str = line[idx:].strip()
                    try:
                        ev = json.loads(json_str)
                    except json.JSONDecodeError as exc:
                        log.warning("JSON inválido ignorado (%s): %r", exc, json_str)
                        continue
                    try:
                        processor.handle(ev)
                    except requests.HTTPError as exc:
                        log.error("Erro HTTP: %s", exc)
                    except requests.ConnectionError:
                        log.error("Backend inacessível. Verifique se o servidor está rodando.")
                    except Exception as exc:
                        log.error("Erro: %s", exc, exc_info=True)

        except serial.SerialException as exc:
            writer.detach()
            log.error("Porta serial: %s. Reconectando em %ds…", exc, RETRY_DELAY_S)
            time.sleep(RETRY_DELAY_S)
        except KeyboardInterrupt:
            writer.detach()
            log.info("Gateway encerrado.")
            break


# ---------------------------------------------------------------------------
# Config  (gateway_config.json)
# ---------------------------------------------------------------------------
def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Configuração salva em {CONFIG_FILE}")


# ---------------------------------------------------------------------------
# Wizard interativo
# ---------------------------------------------------------------------------
def _ask(prompt: str, default: str) -> str:
    value = input(f"  {prompt} [{default}]: ").strip()
    return value if value else default

def _pick(prompt: str, options: list[str]) -> int:
    """Exibe uma lista numerada e retorna o índice (0-based) escolhido."""
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input(f"  {prompt} [1]: ").strip()
        idx = int(raw) if raw.isdigit() else 1
        if 1 <= idx <= len(options):
            return idx - 1
        print(f"  Escolha entre 1 e {len(options)}.")

def run_wizard(saved: dict) -> dict:
    """
    Guia interativo: autentica no EMR, lista robôs e portas seriais,
    e devolve um dict com {url, user, password, robot_code, robot_id, port, baud}.
    """
    sep = "─" * 56

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   Gateway Serial  ESP32-P4  ↔  EMR  (configuração)  ║")
    print("╚══════════════════════════════════════════════════════╝")

    # ── Backend EMR ──────────────────────────────────────────────
    print()
    print("Backend EMR")
    print(sep)
    url  = _ask("URL do servidor", saved.get("url",      "http://127.0.0.1:8765"))
    user = _ask("Utilizador",      saved.get("user",     "teste"))
    pwd  = _ask("Senha",           saved.get("password", "123456"))

    print()
    print("  Conectando ao backend EMR…", end="", flush=True)
    client = EMRClient(url, user, pwd)
    try:
        client.login()
        print(" OK")
    except requests.ConnectionError:
        print(f"\n\n  ERRO: Não foi possível conectar em {url}")
        print("  Verifique se o servidor está rodando: python run_dev.py")
        sys.exit(1)
    except requests.HTTPError as exc:
        print(f"\n\n  ERRO: Autenticação falhou — {exc}")
        sys.exit(1)

    # ── Separadores cadastrados ───────────────────────────────────
    print()
    print("Separadores cadastrados no EMR")
    print(sep)
    robots: list[dict] = client.list_robots()
    if not robots:
        print("  Nenhum separador cadastrado. Cadastre um no painel web antes de continuar.")
        sys.exit(1)

    robot_labels = []
    for r in robots:
        st    = STATUS_LABEL.get(r.get("status", ""), r.get("status", ""))
        os_info = f"  OS: {r['current_os_code']}" if r.get("current_os_code") else ""
        robot_labels.append(f"{r['name']}  (código: {r['code']})  [{st}]{os_info}")

    robot_idx = _pick("Escolha o separador", robot_labels)
    chosen_robot = robots[robot_idx]
    print(f"  → {chosen_robot['name']}  (ID={chosen_robot['id']}, código={chosen_robot['code']})")

    # ── Portas seriais ────────────────────────────────────────────
    print()
    print("Porta serial do ESP32")
    print(sep)
    com_ports = serial.tools.list_ports.comports()
    if not com_ports:
        print("  Nenhuma porta serial detectada.")
        print("  Conecte o ESP32 via USB e tente novamente.")
        sys.exit(1)

    port_labels = [f"{p.device:<10} {p.description}" for p in com_ports]
    # pré-seleciona a porta salva se ainda existir
    default_port_idx = 1
    saved_port = saved.get("port", "")
    for i, p in enumerate(com_ports):
        if p.device == saved_port:
            default_port_idx = i + 1
            break

    # re-exibe com índice correto
    for i, lbl in enumerate(port_labels, 1):
        print(f"  {i}. {lbl}")
    while True:
        raw = input(f"  Escolha a porta [{default_port_idx}]: ").strip()
        idx = int(raw) if raw.isdigit() else default_port_idx
        if 1 <= idx <= len(com_ports):
            break
        print(f"  Escolha entre 1 e {len(com_ports)}.")
    chosen_port = com_ports[idx - 1].device
    print(f"  → {chosen_port}")

    baud = int(_ask("Baud rate", str(saved.get("baud", 115200))))

    # ── Salvar configuração ───────────────────────────────────────
    print()
    save = _ask("Salvar configuração para próxima vez? (s/n)", "s").lower()
    cfg = {
        "url":        url,
        "user":       user,
        "password":   pwd,
        "robot_code": chosen_robot["code"],
        "robot_id":   chosen_robot["id"],
        "port":       chosen_port,
        "baud":       baud,
    }
    if save.startswith("s"):
        save_config(cfg)

    print()
    print(sep)
    print(f"  Separador : {chosen_robot['name']} ({chosen_robot['code']})")
    print(f"  Porta     : {chosen_port} @ {baud} baud")
    print(f"  Backend   : {url}")
    print(sep)
    print()
    return cfg


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gateway serial bidirecional ESP32-P4 ↔ Backend EMR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Sem argumentos: modo interativo (lista separadores e portas seriais).

Modo direto (sem assistente):
  python serial_gateway.py --port COM5 --robot-code ESP32-P4-001

Outros exemplos:
  python serial_gateway.py --list-ports
  python serial_gateway.py --list-robots --url http://192.168.1.10:8765
        """,
    )
    parser.add_argument("--port",       default=None,  help="Porta serial (ex.: COM3, /dev/ttyUSB0)")
    parser.add_argument("--baud",       type=int, default=115200)
    parser.add_argument("--url",        default="http://127.0.0.1:8765")
    parser.add_argument("--user",       default="teste")
    parser.add_argument("--password",   default="123456")
    parser.add_argument("--robot-code", default=None,  help="Código do separador no EMR")
    parser.add_argument("--list-ports", action="store_true", help="Lista portas seriais e sai")
    parser.add_argument("--list-robots",action="store_true", help="Lista separadores do EMR e sai")
    parser.add_argument("--debug",      action="store_true", help="Logs detalhados")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # ── --list-ports ─────────────────────────────────────────────
    if args.list_ports:
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("Nenhuma porta serial detectada.")
        else:
            for p in ports:
                print(f"  {p.device:<10} {p.description}")
        sys.exit(0)

    # ── --list-robots ─────────────────────────────────────────────
    if args.list_robots:
        client = EMRClient(args.url, args.user, args.password)
        try:
            client.login()
        except Exception as exc:
            print(f"Erro ao conectar: {exc}")
            sys.exit(1)
        for r in client.list_robots():
            st = STATUS_LABEL.get(r.get("status", ""), r.get("status", ""))
            print(f"  [{r['id']:3}] {r['code']:<20} {r['name']:<30} {st}")
        sys.exit(0)

    # ── Modo interativo (sem --port ou sem --robot-code) ──────────
    interactive = args.port is None or args.robot_code is None
    if interactive:
        saved = load_config()
        cfg   = run_wizard(saved)
        url        = cfg["url"]
        user       = cfg["user"]
        password   = cfg["password"]
        robot_code = cfg["robot_code"]
        robot_id   = cfg["robot_id"]
        port       = cfg["port"]
        baud       = cfg["baud"]
        client     = EMRClient(url, user, password)
        try:
            client.login()
        except Exception as exc:
            log.error("Falha ao reautenticar: %s", exc)
            sys.exit(1)
    else:
        # ── Modo direto (todos os args na linha de comando) ───────
        url, user, password = args.url, args.user, args.password
        port, baud          = args.port, args.baud
        robot_code          = args.robot_code
        client              = EMRClient(url, user, password)
        log.info("Autenticando no backend EMR…")
        try:
            client.login()
        except requests.ConnectionError:
            log.error("Não foi possível conectar ao backend EMR em %s.", url)
            sys.exit(1)
        except requests.HTTPError as exc:
            log.error("Falha de autenticação: %s", exc)
            sys.exit(1)
        robot = client.find_robot_by_code(robot_code)
        if robot is None:
            log.error("Robô '%s' não encontrado no EMR.", robot_code)
            sys.exit(1)
        robot_id = robot["id"]
        log.info("Robô '%s' encontrado → ID=%d", robot_code, robot_id)

    log.info("=== Gateway ESP32-P4 ↔ EMR iniciado ===")
    log.info("Separador : %s (ID=%d)", robot_code, robot_id)
    log.info("Porta     : %s @ %d baud", port, baud)

    writer    = SerialWriter()
    processor = EventProcessor(client, robot_id)
    poller    = EMRPoller(client, writer, robot_id)
    run_serial_loop(port, baud, processor, writer, poller)


if __name__ == "__main__":
    main()
