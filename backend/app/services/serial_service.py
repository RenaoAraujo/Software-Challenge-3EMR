"""serial_service.py — Gerencia a conexão serial com o ESP32 como serviço interno do backend.

O _InternalClient opera diretamente sobre as camadas de serviço/repositório Python,
eliminando a chamada HTTP circular que o gateway standalone usava.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import serial
import serial.tools.list_ports
from sqlalchemy import select

from app.database import SessionLocal
from app.models.entities import Robot, RobotStatus, ServiceOrder, ServiceOrderStatus
from app.repositories.robot_repository import RobotRepository
from app.schemas.robot import RobotUpdateBody
from app.services.assignment_service import AssignmentService
from app.services.os_dispatch import medicine_first_name
from app.services.product_catalog import random_products
from app.services.robot_service import RobotService

log = logging.getLogger("serial_service")

BRIDGE_PREFIX = "BRIDGE:"
CMD_PREFIX = "CMD:"
POLL_INTERVAL = 0.3
RETRY_DELAY_S = 3


# ---------------------------------------------------------------------------
# Estrutura de status exposta pela API
# ---------------------------------------------------------------------------
@dataclass
class SerialStatus:
    connected: bool = False
    port: str | None = None
    baud: int = 115200
    robot_id: int | None = None
    robot_name: str | None = None
    robot_code: str | None = None
    error: str | None = None
    connecting: bool = False


# ---------------------------------------------------------------------------
# Cliente interno: chama os serviços Python diretamente (sem HTTP)
# ---------------------------------------------------------------------------
class _InternalClient:
    """Substitui o _EMRClient HTTP — cada operação abre e fecha sua própria sessão."""

    def __init__(self, robot_id: int) -> None:
        self._robot_id = robot_id

    # ── helpers ──────────────────────────────────────────────────────────────
    def _db(self):
        return SessionLocal()

    # ── leitura do robô (para o Poller) ──────────────────────────────────────
    def get_robot_state(self) -> dict | None:
        db = self._db()
        try:
            robot: Robot | None = RobotRepository(db).get_by_id(self._robot_id)
            if robot is None:
                return None
            order = robot.current_order
            return {
                "status": robot.status,
                "units_separated": robot.units_separated,
                "current_order": {
                    "os_code": order.os_code,
                    "expected_units": order.expected_units,
                    "client_name": order.client_name or "",
                    "medicamento": medicine_first_name(order.medicines_json),
                } if order is not None else None,
            }
        finally:
            db.close()

    # ── últ. OS encerrada por código (para o Poller detectar conclusão/cancel) ─
    def get_last_closed_order(self, os_code: str) -> dict | None:
        db = self._db()
        try:
            stmt = (
                select(ServiceOrder)
                .where(
                    ServiceOrder.os_code == os_code,
                    ServiceOrder.status.in_([
                        ServiceOrderStatus.COMPLETED.value,
                        ServiceOrderStatus.CANCELLED.value,
                    ]),
                )
                .order_by(ServiceOrder.id.desc())
                .limit(1)
            )
            order: ServiceOrder | None = db.scalars(stmt).first()
            if order is None:
                return None
            return {
                "situacao": "concluida" if order.status == ServiceOrderStatus.COMPLETED.value else "cancelada",
                "erro_descricao": order.cancel_error_description,
            }
        finally:
            db.close()

    # ── garante que o robô está idle antes de atribuir OS ────────────────────
    def ensure_robot_idle(self) -> None:
        db = self._db()
        try:
            robot = RobotRepository(db).get_by_id(self._robot_id)
            if robot is None:
                return
            if robot.status in (
                RobotStatus.OFFLINE.value,
                RobotStatus.MAINTENANCE.value,
                RobotStatus.ERROR.value,
            ):
                log.info("Robô %d estava '%s' — alterando para idle", self._robot_id, robot.status)
                RobotService(db).update_robot(
                    self._robot_id,
                    RobotUpdateBody(status="idle"),  # type: ignore[arg-type]
                )
        finally:
            db.close()

    # ── cria OS e atribui ao robô ─────────────────────────────────────────────
    def create_os_and_assign(self, os_code: str, client_name: str, total: int) -> None:
        db = self._db()
        try:
            svc = AssignmentService(db)
            try:
                svc.create_manual_order_and_assign(
                    self._robot_id, os_code, client_name, total,
                )
                log.info("OS '%s' criada e atribuída ao robô %d", os_code, self._robot_id)
            except Exception as exc:
                msg = str(exc)
                if "cancelada" in msg.lower() or "cancelled" in msg.lower() or "já existe" in msg.lower():
                    log.warning("OS '%s' já existia cancelada — reabrindo (restart)", os_code)
                    svc.create_manual_order_and_assign(
                        self._robot_id, os_code, client_name, total,
                        reopen_cancelled="restart",
                    )
                    log.info("OS '%s' reaberta (restart) no robô %d", os_code, self._robot_id)
                else:
                    raise
        finally:
            db.close()

    # ── atualiza unidades separadas ───────────────────────────────────────────
    def update_units(self, units: int) -> None:
        db = self._db()
        try:
            # Salva o order_id ANTES da chamada (auto-complete pode zerar current_order_id)
            robot_pre = RobotRepository(db).get_by_id(self._robot_id)
            order_id = robot_pre.current_order_id if robot_pre else None

            RobotService(db).update_units_separated(self._robot_id, units)
            log.info("Progresso: %d unidades (robô %d)", units, self._robot_id)

            # Seleciona aleatoriamente o remédio coletado e registra o timestamp exato
            if order_id is not None:
                order = db.get(ServiceOrder, order_id)
                if order is not None:
                    try:
                        items = json.loads(order.medicines_json or "[]")
                        idx = units - 1  # índice base-0 do remédio recém-coletado
                        now_ts = datetime.now(UTC).isoformat()
                        if idx < len(items):
                            # Slot já existe (ex: OS retomada) — só registra timestamp
                            if isinstance(items[idx], dict) and not items[idx].get("picked_at"):
                                items[idx]["picked_at"] = now_ts
                                order.medicines_json = json.dumps(items, ensure_ascii=False)
                                db.add(order)
                                db.commit()
                        else:
                            # Seleção aleatória disparada pelo pick da ESP32
                            [new_med] = random_products(1)
                            new_med["picked_at"] = now_ts
                            items.append(new_med)
                            order.medicines_json = json.dumps(items, ensure_ascii=False)
                            db.add(order)
                            db.commit()
                            log.info(
                                "Pick ESP32 #%d → %s (%s)",
                                units, new_med.get("remedio"), new_med.get("remedio_id"),
                            )
                    except Exception as exc:
                        log.warning("Falha ao registrar remédio coletado: %s", exc)
        except ValueError as exc:
            log.debug("update_units ignorado: %s", exc)
        finally:
            db.close()

    # ── conclui a OS atual ────────────────────────────────────────────────────
    def complete_os(self) -> None:
        db = self._db()
        try:
            RobotService(db).complete_current_order(self._robot_id)
            log.info("OS concluída no robô %d", self._robot_id)
        except ValueError as exc:
            log.info("complete_os ignorado (provavelmente já concluída): %s", exc)
        finally:
            db.close()

    # ── encontra ou cria robô pelo código (usado na auto-descoberta) ─────────
    def find_or_create_robot_by_code(self, code: str, name: str) -> int:
        db = self._db()
        try:
            robot: Robot | None = db.scalar(select(Robot).where(Robot.code == code))
            if robot is None:
                robot = Robot(code=code, name=name, status=RobotStatus.IDLE.value)
                db.add(robot)
                db.commit()
                db.refresh(robot)
                log.info("Auto-descoberta: robô '%s' (%s) criado (id=%d)", name, code, robot.id)
            else:
                if robot.name != name:
                    robot.name = name
                    db.add(robot)
                    db.commit()
                log.info("Auto-descoberta: robô '%s' (%s) encontrado (id=%d)", name, code, robot.id)
            self._robot_id = robot.id
            return robot.id
        finally:
            db.close()

    # ── pausa a OS atual ──────────────────────────────────────────────────────
    def pause_os(self) -> None:
        db = self._db()
        try:
            RobotService(db).pause_separation(self._robot_id)
            log.info("OS pausada no robô %d (solicitado pela ESP32)", self._robot_id)
        except ValueError as exc:
            log.info("pause_os ignorado: %s", exc)
        finally:
            db.close()

    # ── retoma a OS pausada ───────────────────────────────────────────────────
    def resume_os(self) -> None:
        db = self._db()
        try:
            RobotService(db).resume_separation(self._robot_id)
            log.info("OS retomada no robô %d (solicitado pela ESP32)", self._robot_id)
        except ValueError as exc:
            log.info("resume_os ignorado: %s", exc)
        finally:
            db.close()

    # ── cancela a OS atual ────────────────────────────────────────────────────
    def cancel_os(self, reason: str) -> None:
        db = self._db()
        try:
            RobotService(db).cancel_current_order(
                self._robot_id,
                reason_code="OUTROS",
                detail=(reason.strip() or "Cancelado pelo separador"),
            )
            log.info("OS cancelada no robô %d — motivo: %s", self._robot_id, reason)
        except ValueError as exc:
            log.warning("cancel_os falhou: %s", exc)
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Escrita thread-safe na serial
# ---------------------------------------------------------------------------
class _SerialWriter:
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
        line = CMD_PREFIX + json.dumps(cmd, ensure_ascii=False, separators=(',', ':')) + "\n"
        with self._lock:
            if self._port is None or not self._port.is_open:
                return False
            try:
                self._port.write(line.encode("utf-8"))
                return True
            except serial.SerialException as exc:
                log.error("Erro ao escrever na serial: %s", exc)
                return False


# ---------------------------------------------------------------------------
# Processador de eventos BRIDGE (ESP32 → painel)
# ---------------------------------------------------------------------------
class _EventProcessor:
    def __init__(
        self,
        client: _InternalClient,
        robot_code: str = "",
        on_pong: Any = None,
    ) -> None:
        self._c = client
        self._robot_code = robot_code
        self._on_pong = on_pong  # callback(code, name) chamado ao receber pong

    def handle(self, ev: dict) -> None:
        event = ev.get("ev", "")
        os_num = ev.get("num", "?")

        bridge_robot = ev.get("robot", "")

        # Pong: auto-descoberta de identidade da ESP32
        if event == "pong":
            code = bridge_robot or ev.get("robot", "")
            name = ev.get("name", code)
            log.info("BRIDGE pong recebido: robot='%s' name='%s'", code, name)
            if self._on_pong and code:
                self._on_pong(code, name)
            return

        # Valida o campo robot contra o código registrado no banco
        if bridge_robot and self._robot_code and bridge_robot != self._robot_code:
            log.warning(
                "BRIDGE: campo robot='%s' não corresponde ao separador registrado '%s'. "
                "Verifique BRIDGE_ROBOT_CODE no firmware.",
                bridge_robot, self._robot_code,
            )

        if event == "os_start":
            client_name = ev.get("client", "")
            total = int(ev.get("total", 1))
            log.info("[BRIDGE os_start] OS=%s cliente='%s' total=%d", os_num, client_name, total)
            self._c.ensure_robot_idle()
            self._c.create_os_and_assign(os_num, client_name, total)

        elif event == "unit":
            done = int(ev.get("done", 0))
            log.info("[BRIDGE unit] OS=%s done=%d", os_num, done)
            self._c.update_units(done)

        elif event == "os_complete":
            done = int(ev.get("done", 0))
            log.info("[BRIDGE os_complete] OS=%s done=%d", os_num, done)
            self._c.update_units(done)
            self._c.complete_os()

        elif event == "os_cancel":
            done = int(ev.get("done", 0))
            reason = str(ev.get("reason", ""))
            log.info("[BRIDGE os_cancel] OS=%s done=%d reason='%s'", os_num, done, reason)
            self._c.update_units(done)
            self._c.cancel_os(reason)

        elif event == "os_pause":
            log.info("[BRIDGE os_pause] OS=%s", os_num)
            self._c.pause_os()

        elif event == "os_resume":
            log.info("[BRIDGE os_resume] OS=%s", os_num)
            self._c.resume_os()

        else:
            log.debug("Evento desconhecido: %s", event)


# ---------------------------------------------------------------------------
# Poller: detecta mudanças no painel e envia CMD ao ESP32
# ---------------------------------------------------------------------------
class _EMRPoller:
    def __init__(self, client: _InternalClient, writer: _SerialWriter) -> None:
        self._c = client
        self._writer = writer
        self._prev_os_code: str | None = None
        self._prev_units: int = 0
        self._prev_status: str = ""

    def tick(self) -> None:
        state = self._c.get_robot_state()
        if state is None:
            return

        order = state.get("current_order")
        curr_os_code = order.get("os_code") if order else None
        curr_units = int(state.get("units_separated") or 0)
        curr_status = str(state.get("status") or "")

        if curr_os_code and curr_os_code != self._prev_os_code:
            # Nova OS atribuída → envia os_assign
            total = int(order.get("expected_units") or 1) if order else 1
            client_name = order.get("client_name", "") if order else ""
            self._writer.send_cmd({
                "cmd": "os_assign",
                "num": curr_os_code,
                "client": client_name,
                "total": total,
                "os": curr_os_code,
                "quantidade": total,
                "cliente": client_name,
                "medicamento": (order or {}).get("medicamento") or "",
            })

        elif self._prev_os_code and not curr_os_code:
            # OS desapareceu → concluída ou cancelada
            closed = self._c.get_last_closed_order(self._prev_os_code)
            if closed and closed.get("situacao") == "concluida":
                self._writer.send_cmd({
                    "cmd": "os_complete", "num": self._prev_os_code,
                    "done": self._prev_units,
                })
            else:
                motivo = (closed.get("erro_descricao") or "Cancelado pelo painel web") if closed else "Cancelado pelo painel web"
                self._writer.send_cmd({
                    "cmd": "os_cancel", "num": self._prev_os_code,
                    "done": self._prev_units, "reason": motivo,
                })

        elif curr_os_code and curr_os_code == self._prev_os_code:
            # Mesma OS — verifica mudança de pausa/retomada
            if curr_status == "paused" and self._prev_status != "paused":
                self._writer.send_cmd({"cmd": "os_pause", "num": curr_os_code})
                log.info("Poller: enviando os_pause para %s", curr_os_code)
            elif curr_status == "running" and self._prev_status == "paused":
                self._writer.send_cmd({"cmd": "os_resume", "num": curr_os_code})
                log.info("Poller: enviando os_resume para %s", curr_os_code)

        self._prev_os_code = curr_os_code
        self._prev_units = curr_units
        self._prev_status = curr_status

    def run(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            try:
                self.tick()
            except Exception as exc:
                log.error("Poller: exceção: %s", exc, exc_info=True)
            stop_event.wait(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Serviço singleton gerenciado pelo backend
# ---------------------------------------------------------------------------
class SerialGatewayService:
    """Controla a conexão serial do ESP32 dentro do processo do backend."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event: threading.Event | None = None
        self._thread: threading.Thread | None = None
        self.status = SerialStatus()

    @staticmethod
    def list_ports() -> list[dict]:
        return [
            {"device": p.device, "description": p.description or p.device}
            for p in serial.tools.list_ports.comports()
        ]

    def connect(self, *, port: str, baud: int = 115200, robot_id: int, robot_name: str) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise RuntimeError("Gateway já está rodando. Desconecte primeiro.")

            self.status = SerialStatus(
                connecting=True, port=port, baud=baud,
                robot_id=robot_id, robot_name=robot_name,
            )
            stop_event = threading.Event()
            self._stop_event = stop_event

            t = threading.Thread(
                target=self._run,
                args=(port, baud, robot_id, robot_name, stop_event),
                daemon=True,
                name="serial_gateway",
            )
            self._thread = t
            t.start()

    def disconnect(self) -> None:
        with self._lock:
            if self._stop_event:
                self._stop_event.set()
            self._thread = None
            self._stop_event = None
            self.status = SerialStatus()

    def _run(
        self,
        port: str,
        baud: int,
        robot_id: int,
        robot_name: str,
        stop_event: threading.Event,
    ) -> None:
        client = _InternalClient(robot_id)

        # Busca o código do robô para validar o campo robot nos eventos BRIDGE
        robot_code = ""
        try:
            db = SessionLocal()
            try:
                robot_obj = RobotRepository(db).get_by_id(robot_id)
                robot_code = robot_obj.code if robot_obj else ""
            finally:
                db.close()
        except Exception as exc:
            log.warning("Não foi possível buscar o código do robô: %s", exc)

        writer = _SerialWriter()
        processor = _EventProcessor(client, robot_code)
        poller = _EMRPoller(client, writer)
        poll_started = False

        log.info("Gateway: abrindo porta %s @ %d baud…", port, baud)

        while not stop_event.is_set():
            try:
                with serial.Serial(port, baud, timeout=1) as ser:
                    log.info("Gateway: porta %s aberta.", port)
                    writer.attach(ser)
                    with self._lock:
                        self.status = SerialStatus(
                            connected=True, port=port, baud=baud,
                            robot_id=robot_id, robot_name=robot_name,
                            robot_code=robot_code,
                        )

                    # Envia identidade do robô para a ESP32 atualizar a aba Dispositivo
                    writer.send_cmd({
                        "cmd": "set_device",
                        "name": robot_name,
                        "code": robot_code,
                    })
                    log.info("CMD:set_device enviado → name='%s' code='%s'", robot_name, robot_code)

                    if not poll_started:
                        threading.Thread(
                            target=poller.run,
                            args=(stop_event,),
                            daemon=True,
                            name="serial_poller",
                        ).start()
                        poll_started = True

                    while not stop_event.is_set():
                        raw = ser.readline()
                        if not raw:
                            continue
                        line = raw.decode("utf-8", errors="replace").strip()
                        if BRIDGE_PREFIX not in line:
                            continue
                        idx = line.index(BRIDGE_PREFIX) + len(BRIDGE_PREFIX)
                        json_str = line[idx:].strip()
                        try:
                            ev = json.loads(json_str)
                        except json.JSONDecodeError as exc:
                            log.warning("JSON inválido: %s — %r", exc, json_str)
                            continue
                        try:
                            processor.handle(ev)
                        except Exception as exc:
                            log.error("Erro ao processar evento: %s", exc, exc_info=True)

            except serial.SerialException as exc:
                writer.detach()
                if stop_event.is_set():
                    break
                err_msg = str(exc)
                log.error("Porta serial: %s. Reconectando em %ds…", err_msg, RETRY_DELAY_S)
                with self._lock:
                    self.status = SerialStatus(
                        port=port, baud=baud,
                        robot_id=robot_id, robot_name=robot_name,
                        robot_code=robot_code,
                        error=f"Porta perdida: {err_msg}. Reconectando…",
                    )
                stop_event.wait(RETRY_DELAY_S)

        writer.detach()
        log.info("Gateway: encerrado.")


# Instância singleton usada em todo o backend
serial_gateway = SerialGatewayService()
