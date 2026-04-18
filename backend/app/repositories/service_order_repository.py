from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import ServiceOrder, ServiceOrderStatus


class ServiceOrderRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, order_id: int) -> ServiceOrder | None:
        return self._db.get(ServiceOrder, order_id)

    def list_assignable(self) -> list[ServiceOrder]:
        stmt = (
            select(ServiceOrder)
            .where(
                ServiceOrder.status.in_(
                    [ServiceOrderStatus.PENDING.value, ServiceOrderStatus.IN_PROGRESS.value]
                )
            )
            .order_by(ServiceOrder.os_code)
        )
        return list(self._db.scalars(stmt).all())

    def list_completed_by_robot_between(
        self,
        robot_id: int,
        start_utc: datetime,
        end_utc_exclusive: datetime,
    ) -> list[ServiceOrder]:
        stmt = (
            select(ServiceOrder)
            .where(
                and_(
                    ServiceOrder.completed_by_robot_id == robot_id,
                    ServiceOrder.status == ServiceOrderStatus.COMPLETED.value,
                    ServiceOrder.completed_at.is_not(None),
                    ServiceOrder.completed_at >= start_utc,
                    ServiceOrder.completed_at < end_utc_exclusive,
                )
            )
            .order_by(ServiceOrder.completed_at.desc())
        )
        return list(self._db.scalars(stmt).all())

    def count_cancelled_by_robot_between(
        self,
        robot_id: int,
        start_utc: datetime,
        end_utc_exclusive: datetime,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(ServiceOrder)
            .where(
                and_(
                    ServiceOrder.status == ServiceOrderStatus.CANCELLED.value,
                    ServiceOrder.cancelled_by_robot_id == robot_id,
                    ServiceOrder.cancelled_at.is_not(None),
                    ServiceOrder.cancelled_at >= start_utc,
                    ServiceOrder.cancelled_at < end_utc_exclusive,
                )
            )
        )
        return int(self._db.scalar(stmt) or 0)

    def count_ended_with_pause_by_robot_between(
        self,
        robot_id: int,
        start_utc: datetime,
        end_utc_exclusive: datetime,
    ) -> int:
        """OS concluídas ou canceladas no período neste separador com ao menos uma pausa registrada."""
        completed = and_(
            ServiceOrder.status == ServiceOrderStatus.COMPLETED.value,
            ServiceOrder.completed_by_robot_id == robot_id,
            ServiceOrder.completed_at.is_not(None),
            ServiceOrder.completed_at >= start_utc,
            ServiceOrder.completed_at < end_utc_exclusive,
            ServiceOrder.pause_count > 0,
        )
        cancelled = and_(
            ServiceOrder.status == ServiceOrderStatus.CANCELLED.value,
            ServiceOrder.cancelled_by_robot_id == robot_id,
            ServiceOrder.cancelled_at.is_not(None),
            ServiceOrder.cancelled_at >= start_utc,
            ServiceOrder.cancelled_at < end_utc_exclusive,
            ServiceOrder.pause_count > 0,
        )
        stmt = select(func.count()).select_from(ServiceOrder).where(or_(completed, cancelled))
        return int(self._db.scalar(stmt) or 0)
