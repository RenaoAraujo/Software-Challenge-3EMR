"""Preenche a tabela order_events a partir de OS já existentes no banco.

Executado uma única vez (idempotente): enquanto não houver nenhum evento gravado,
derivamos os eventos históricos dos campos hoje presentes em ServiceOrder:
- `completed_at` → evento COMPLETED
- `cancelled_at` → evento CANCELLED
- `pause_count > 0` em OS já concluída/cancelada → N eventos PAUSED
  (usando o `occurred_at` do evento final como aproximação, já que não temos
  o timestamp individual de cada pausa).

Depois dessa primeira passada, as contagens usam apenas eventos gravados em
tempo real pelo `RobotService`.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import OrderEvent, OrderEventType, ServiceOrder, ServiceOrderStatus
from app.repositories.order_event_repository import OrderEventRepository


def backfill_order_events_if_empty(db: Session) -> int:
    """Se a tabela order_events estiver vazia, grava eventos históricos a partir de service_orders.

    Retorna a quantidade de eventos gravados.
    """
    existing = db.scalar(select(func.count()).select_from(OrderEvent)) or 0
    if int(existing) > 0:
        return 0

    repo = OrderEventRepository(db)
    created = 0

    stmt = select(ServiceOrder).where(
        ServiceOrder.status.in_(
            (ServiceOrderStatus.COMPLETED.value, ServiceOrderStatus.CANCELLED.value)
        )
    )
    orders = list(db.scalars(stmt).all())

    for o in orders:
        n_pausas = max(0, int(o.pause_count or 0))
        if o.status == ServiceOrderStatus.COMPLETED.value and o.completed_at is not None:
            repo.record(
                order_id=o.id,
                order_code=o.os_code,
                event_type=OrderEventType.COMPLETED,
                occurred_at=o.completed_at,
                robot_id=o.completed_by_robot_id,
                robot_name=o.completed_by_robot_name,
                pause_count=n_pausas,
                meta={"completed_units": int(o.completed_units or 0)},
            )
            created += 1
            ref_time = o.completed_at
        elif o.status == ServiceOrderStatus.CANCELLED.value and o.cancelled_at is not None:
            repo.record(
                order_id=o.id,
                order_code=o.os_code,
                event_type=OrderEventType.CANCELLED,
                occurred_at=o.cancelled_at,
                robot_id=o.cancelled_by_robot_id,
                robot_name=o.cancelled_by_robot_name,
                pause_count=n_pausas,
                meta={
                    "reason_code": o.cancel_error_code,
                    "reason_description": o.cancel_error_description,
                    "separated_units": int(o.cancelled_separated_units or 0),
                },
            )
            created += 1
            ref_time = o.cancelled_at
        else:
            continue

        for _ in range(n_pausas):
            repo.record(
                order_id=o.id,
                order_code=o.os_code,
                event_type=OrderEventType.PAUSED,
                occurred_at=ref_time,
                robot_id=o.completed_by_robot_id or o.cancelled_by_robot_id,
                robot_name=o.completed_by_robot_name or o.cancelled_by_robot_name,
                meta={"backfilled": True},
            )
            created += 1

    if created:
        db.commit()
    return created
