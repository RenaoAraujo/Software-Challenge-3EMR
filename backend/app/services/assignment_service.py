import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Robot, RobotStatus, ServiceOrder, ServiceOrderStatus
from app.repositories.robot_repository import RobotRepository
from app.repositories.service_order_repository import ServiceOrderRepository


class AssignmentError(Exception):
    def __init__(self, message: str, code: str = "assignment_error") -> None:
        super().__init__(message)
        self.code = code


class AssignmentService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._robots = RobotRepository(db)
        self._orders = ServiceOrderRepository(db)

    def assign_order_to_robot(self, robot_id: int, service_order_id: int) -> None:
        robot = self._robots.get_by_id(robot_id)
        if robot is None:
            raise AssignmentError("Robô não encontrado.", "robot_not_found")

        order = self._orders.get_by_id(service_order_id)
        if order is None:
            raise AssignmentError("Ordem de serviço não encontrada.", "order_not_found")

        if robot.status == RobotStatus.OFFLINE.value:
            raise AssignmentError(
                "Separador offline. Cadastro no sistema não exige equipamento ligado; "
                "quando estiver pronto, defina o status como ocioso (idle) e envie a OS.",
                "robot_offline",
            )
        if robot.status == RobotStatus.MAINTENANCE.value:
            raise AssignmentError(
                "Robô em manutenção. Não é possível atribuir OS.",
                "robot_maintenance",
            )
        if robot.status == RobotStatus.ERROR.value:
            raise AssignmentError(
                "Robô em estado de erro. Corrija antes de nova atribuição.",
                "robot_error",
            )
        if (
            robot.status in (RobotStatus.RUNNING.value, RobotStatus.PAUSED.value)
            and robot.current_order_id
        ):
            raise AssignmentError(
                "Robô ocupado com outra OS. Finalize ou cancele antes.",
                "robot_busy",
            )

        if order.status not in (
            ServiceOrderStatus.PENDING.value,
            ServiceOrderStatus.IN_PROGRESS.value,
        ):
            raise AssignmentError(
                "Somente OS pendentes ou em andamento podem ser enviadas ao robô.",
                "invalid_order_status",
            )

        other = self._db.scalar(
            select(Robot).where(
                Robot.current_order_id == order.id,
                Robot.id != robot_id,
            )
        )
        if other is not None:
            raise AssignmentError(
                "Esta OS já está vinculada a outro robô.",
                "order_assigned_elsewhere",
            )

        now = datetime.now(UTC)
        robot.current_order_id = order.id
        robot.job_started_at = now
        robot.paused_at = None
        robot.elapsed_pause_seconds = 0
        robot.units_separated = 0
        robot.status = RobotStatus.RUNNING.value
        order.status = ServiceOrderStatus.IN_PROGRESS.value
        order.assigned_at = now
        order.pause_count = 0

        self._db.add(robot)
        self._db.add(order)
        self._db.commit()

    def create_manual_order_and_assign(
        self,
        robot_id: int,
        os_code: str,
        client_name: str,
        quantidade_remedios: int,
    ) -> ServiceOrder:
        """Cria uma OS de teste com itens sintéticos e já envia ao separador."""
        code = (os_code or "").strip()
        if not code:
            raise AssignmentError("Informe o número da OS.", "invalid_os_code")
        if quantidade_remedios < 1:
            raise AssignmentError("Informe ao menos 1 remédio.", "invalid_quantity")

        dup = self._db.scalar(select(ServiceOrder).where(ServiceOrder.os_code == code))
        if dup is not None:
            raise AssignmentError("Já existe uma OS com este número.", "duplicate_os")

        meds = [f"Medicamento (teste) {i + 1}" for i in range(quantidade_remedios)]
        order = ServiceOrder(
            os_code=code,
            description="OS manual — teste",
            client_name=(client_name or "").strip(),
            expected_units=quantidade_remedios,
            status=ServiceOrderStatus.PENDING.value,
            medicines_json=json.dumps(meds, ensure_ascii=False),
        )
        self._db.add(order)
        self._db.flush()

        self.assign_order_to_robot(robot_id, order.id)
        self._db.refresh(order)
        return order
