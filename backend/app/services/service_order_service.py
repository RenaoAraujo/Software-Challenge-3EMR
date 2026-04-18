from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Robot, RobotStatus
from app.repositories.service_order_repository import ServiceOrderRepository


class ServiceOrderService:
    """Operações que alteram ordens de serviço e vínculos com separadores."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._orders = ServiceOrderRepository(db)

    def delete_order(self, order_id: int) -> bool:
        """Remove a OS do banco e desvincula de qualquer separador que a referencie."""
        order = self._orders.get_by_id(order_id)
        if order is None:
            return False

        stmt = select(Robot).where(Robot.current_order_id == order_id)
        for robot in self._db.scalars(stmt).all():
            robot.current_order_id = None
            robot.job_started_at = None
            robot.paused_at = None
            robot.elapsed_pause_seconds = 0
            robot.units_separated = 0
            if robot.status in (RobotStatus.RUNNING.value, RobotStatus.PAUSED.value):
                robot.status = RobotStatus.IDLE.value
            self._db.add(robot)

        self._db.delete(order)
        self._db.commit()
        return True
