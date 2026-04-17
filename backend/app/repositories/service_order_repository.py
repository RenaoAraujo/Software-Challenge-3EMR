from sqlalchemy import select
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
