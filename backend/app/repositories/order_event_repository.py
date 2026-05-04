"""Repositório de OrderEvent: registro permanente de cancelamentos, conclusões e pausas de OS."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.entities import OrderEvent, OrderEventType

# Tipos de evento considerados "conclusão" (manual ou automática).
COMPLETION_EVENT_TYPES: tuple[str, ...] = (
    OrderEventType.COMPLETED.value,
    OrderEventType.COMPLETED_AUTO.value,
)


class OrderEventRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def record(
        self,
        *,
        order_id: int | None,
        order_code: str,
        event_type: OrderEventType | str,
        occurred_at: datetime,
        robot_id: int | None,
        robot_name: str | None,
        pause_count: int | None = None,
        meta: dict[str, Any] | None = None,
    ) -> OrderEvent:
        """Cria e persiste um evento imutável. Não faz commit — deixa a cargo da transação em curso."""
        et = event_type.value if isinstance(event_type, OrderEventType) else str(event_type)
        row = OrderEvent(
            order_id=order_id,
            order_code=(order_code or "").strip()[:64],
            event_type=et[:32],
            occurred_at=occurred_at,
            robot_id=robot_id,
            robot_name=(robot_name or None),
            pause_count=pause_count,
            meta_json=json.dumps(meta, ensure_ascii=False) if meta else None,
        )
        self._db.add(row)
        return row

    def _count(
        self,
        *,
        event_types: tuple[str, ...],
        start_utc: datetime,
        end_utc_exclusive: datetime,
        robot_id: int | None = None,
    ) -> int:
        conds = [
            OrderEvent.event_type.in_(event_types),
            OrderEvent.occurred_at >= start_utc,
            OrderEvent.occurred_at < end_utc_exclusive,
        ]
        if robot_id is not None:
            conds.append(OrderEvent.robot_id == robot_id)
        stmt = select(func.count()).select_from(OrderEvent).where(and_(*conds))
        return int(self._db.scalar(stmt) or 0)

    def count_cancelled_between(
        self,
        start_utc: datetime,
        end_utc_exclusive: datetime,
        *,
        robot_id: int | None = None,
    ) -> int:
        return self._count(
            event_types=(OrderEventType.CANCELLED.value,),
            start_utc=start_utc,
            end_utc_exclusive=end_utc_exclusive,
            robot_id=robot_id,
        )

    def count_completed_between(
        self,
        start_utc: datetime,
        end_utc_exclusive: datetime,
        *,
        robot_id: int | None = None,
    ) -> int:
        return self._count(
            event_types=COMPLETION_EVENT_TYPES,
            start_utc=start_utc,
            end_utc_exclusive=end_utc_exclusive,
            robot_id=robot_id,
        )

    def count_paused_between(
        self,
        start_utc: datetime,
        end_utc_exclusive: datetime,
        *,
        robot_id: int | None = None,
    ) -> int:
        return self._count(
            event_types=(OrderEventType.PAUSED.value,),
            start_utc=start_utc,
            end_utc_exclusive=end_utc_exclusive,
            robot_id=robot_id,
        )

    def sum_pause_count_between(
        self,
        *,
        event_types: tuple[str, ...],
        start_utc: datetime,
        end_utc_exclusive: datetime,
        robot_id: int | None = None,
    ) -> int:
        """Soma `pause_count` dos eventos de um dado tipo no período.

        Usado para agregar "pausas das OS concluídas" vs "pausas das OS canceladas":
        cada evento de término (COMPLETED/CANCELLED) carrega o pause_count da execução
        que foi finalizada — mesmo quando a OS é reaberta depois, o evento anterior
        continua contabilizando suas pausas.
        """
        conds = [
            OrderEvent.event_type.in_(event_types),
            OrderEvent.occurred_at >= start_utc,
            OrderEvent.occurred_at < end_utc_exclusive,
        ]
        if robot_id is not None:
            conds.append(OrderEvent.robot_id == robot_id)
        stmt = select(func.coalesce(func.sum(OrderEvent.pause_count), 0)).where(and_(*conds))
        return int(self._db.scalar(stmt) or 0)
