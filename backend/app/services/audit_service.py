from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from app.models.entities import AuditLog

# Grupos de `action` para filtro por “área” (histórico, cancelamento, pausa, etc.)
AUDIT_CATEGORY_ACTIONS: dict[str, tuple[str, ...]] = {
    "historico": ("view_historico", "view_relatorio_os", "export_relatorio_os"),
    "cancelamento": ("os_cancelled",),
    "pausa": ("os_paused",),
    "retomada": ("os_resumed",),
    "conclusao": ("os_completed", "os_completed_auto"),
    "inicio_os": ("os_started",),
    "sessao": ("login", "logout"),
    "contas": (
        "password_changed_self",
        "password_changed_by_admin",
        "user_created",
        "user_promoted_admin",
        "user_demoted_admin",
        "user_updated_by_admin",
    ),
    "os_todas": (
        "os_started",
        "os_completed",
        "os_cancelled",
        "os_paused",
        "os_resumed",
        "os_completed_auto",
    ),
}


def _utc_day_bounds(de: date, ate: date) -> tuple[datetime, datetime]:
    start = datetime(de.year, de.month, de.day, tzinfo=UTC)
    end_exclusive = datetime(ate.year, ate.month, ate.day, tzinfo=UTC) + timedelta(days=1)
    return start, end_exclusive


class AuditService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def log(
        self,
        *,
        user_id: int | None,
        username: str,
        action: str,
        description: str,
        meta: dict[str, Any] | None = None,
    ) -> None:
        row = AuditLog(
            user_id=user_id,
            username=(username or "").strip()[:64] or "—",
            action=action[:64],
            description=description or "",
            meta_json=json.dumps(meta, ensure_ascii=False) if meta else None,
        )
        self._db.add(row)
        self._db.commit()

    def list_recent(self, *, limit: int = 200, offset: int = 0) -> tuple[list[AuditLog], int]:
        return self.list_filtered(
            limit=limit,
            offset=offset,
            username_contains=None,
            category=None,
            de=None,
            ate=None,
        )

    def list_filtered(
        self,
        *,
        limit: int = 200,
        offset: int = 0,
        username_contains: str | None = None,
        category: str | None = None,
        de: date | None = None,
        ate: date | None = None,
    ) -> tuple[list[AuditLog], int]:
        limit = max(1, min(limit, 500))
        offset = max(0, offset)
        conditions = []

        u = (username_contains or "").strip()
        if u:
            conditions.append(func.instr(func.lower(AuditLog.username), func.lower(u)) > 0)

        if de is not None and ate is not None:
            if de > ate:
                raise ValueError("A data inicial não pode ser posterior à data final.")
            start, end_excl = _utc_day_bounds(de, ate)
            conditions.append(AuditLog.created_at >= start)
            conditions.append(AuditLog.created_at < end_excl)
        elif de is not None:
            start = datetime(de.year, de.month, de.day, tzinfo=UTC)
            conditions.append(AuditLog.created_at >= start)
        elif ate is not None:
            end_excl = datetime(ate.year, ate.month, ate.day, tzinfo=UTC) + timedelta(days=1)
            conditions.append(AuditLog.created_at < end_excl)

        c = (category or "").strip()
        if c:
            actions = AUDIT_CATEGORY_ACTIONS.get(c)
            if actions is None:
                raise ValueError(f"Categoria de log inválida: {c!r}.")
            conditions.append(AuditLog.action.in_(actions))

        base = select(AuditLog)
        if conditions:
            base = base.where(and_(*conditions))

        count_stmt = select(func.count()).select_from(AuditLog)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = self._db.scalar(count_stmt) or 0

        stmt = (
            base.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        )
        rows = list(self._db.scalars(stmt).all())
        return rows, int(total)

    def clear_all(self) -> int:
        """Remove todos os registros de auditoria (irreversível)."""
        result = self._db.execute(delete(AuditLog))
        self._db.commit()
        n = result.rowcount
        return int(n) if n is not None else 0
