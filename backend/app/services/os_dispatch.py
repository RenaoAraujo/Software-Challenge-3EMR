"""JSON da OS lançada, enviado à aplicação externa e ao comando serial."""

from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request

from app.config import settings
from app.models.entities import ServiceOrder

log = logging.getLogger("os_dispatch")


def medicine_first_name(medicines_json: str | None) -> str:
    """Primeira palavra do primeiro remédio, em minúsculas. Ex.: «MIOSAN 10MG…» → «miosan»."""
    try:
        data = json.loads(medicines_json or "[]")
    except json.JSONDecodeError:
        return ""
    if not isinstance(data, list) or not data:
        return ""
    item = data[0]
    if isinstance(item, dict):
        raw = str(item.get("remedio") or item.get("nome") or item.get("name") or "")
    else:
        raw = str(item)
    token = raw.strip().split()
    return token[0].casefold() if token else ""


def order_json_payload(order: ServiceOrder) -> dict[str, str | int]:
    return {
        "os": order.os_code,
        "quantidade": int(order.expected_units or 0),
        "cliente": order.client_name or "",
        "medicamento": medicine_first_name(order.medicines_json),
    }


def _post_json(url: str, payload: dict[str, str | int]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            log.info("OS JSON enviada para %s (HTTP %s)", url, response.status)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        log.warning("Falha ao enviar OS JSON para %s: %s", url, exc)


def dispatch_order_json(order: ServiceOrder) -> None:
    """Envia {os, quantidade, cliente, medicamento} para a URL configurada em EMR_OS_JSON_URL."""
    payload = order_json_payload(order)
    log.info("OS JSON: %s", json.dumps(payload, ensure_ascii=False))
    url = (settings.os_json_url or "").strip()
    if not url:
        return
    threading.Thread(target=_post_json, args=(url, payload), daemon=True).start()
