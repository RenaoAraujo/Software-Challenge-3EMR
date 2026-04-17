from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import Robot, RobotStatus, ServiceOrderStatus, is_robot_online
from app.repositories.robot_repository import RobotRepository
from app.schemas.robot import (
    RobotCreateBody,
    RobotDetail,
    RobotSummary,
    RobotUpdateBody,
    ServiceOrderBrief,
)


class RobotService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = RobotRepository(db)

    def list_robots(self, name_contains: str | None = None) -> list[RobotSummary]:
        robots = self._repo.list_all(name_contains=name_contains)
        return [self._to_summary(r) for r in robots]

    def get_robot(self, robot_id: int) -> RobotDetail | None:
        robot = self._repo.get_by_id(robot_id)
        if robot is None:
            return None
        return self._to_detail(robot)

    def create_robot(self, body: RobotCreateBody) -> RobotDetail:
        code = body.code.strip()
        if self._repo.get_by_code(code):
            raise ValueError("Já existe um separador com este código.")
        robot = Robot(
            code=code,
            name=body.name.strip(),
            location=(body.location or "").strip(),
            model=(body.model or "").strip(),
            specifications=body.specifications or "",
            max_units_per_hour=body.max_units_per_hour,
            status=RobotStatus.OFFLINE.value,
        )
        try:
            self._db.add(robot)
            self._db.commit()
            self._db.refresh(robot)
        except IntegrityError:
            self._db.rollback()
            raise ValueError("Código já cadastrado.") from None
        full = self._repo.get_by_id(robot.id)
        assert full is not None
        return self._to_detail(full)

    def update_robot(self, robot_id: int, body: RobotUpdateBody) -> RobotDetail | None:
        robot = self._repo.get_by_id(robot_id)
        if robot is None:
            return None
        data = body.model_dump(exclude_unset=True)
        if not data:
            raise ValueError("Informe ao menos um campo para atualizar.")
        if "code" in data:
            new_code = str(data["code"]).strip()
            if self._repo.get_by_code(new_code, exclude_id=robot_id):
                raise ValueError("Código já usado por outro separador.")
            robot.code = new_code
        if "name" in data:
            robot.name = str(data["name"]).strip()
        if "location" in data:
            robot.location = str(data["location"] or "").strip()
        if "model" in data:
            robot.model = str(data["model"] or "").strip()
        if "specifications" in data:
            robot.specifications = str(data["specifications"] or "")
        if "max_units_per_hour" in data and data["max_units_per_hour"] is not None:
            robot.max_units_per_hour = int(data["max_units_per_hour"])
        if "status" in data and data["status"] is not None:
            if robot.status == RobotStatus.RUNNING.value and robot.current_order_id:
                raise ValueError("Não altere o status enquanto houver OS em execução.")
            robot.status = data["status"]
        try:
            self._db.add(robot)
            self._db.commit()
            self._db.refresh(robot)
        except IntegrityError:
            self._db.rollback()
            raise ValueError("Código já cadastrado.") from None
        full = self._repo.get_by_id(robot_id)
        assert full is not None
        return self._to_detail(full)

    def update_units_separated(self, robot_id: int, units: int) -> RobotDetail | None:
        robot = self._repo.get_by_id(robot_id)
        if robot is None:
            return None
        if robot.status != RobotStatus.RUNNING.value:
            raise ValueError("Só é possível registrar unidades com o robô em operação (running).")
        if units < 0:
            raise ValueError("units_separated não pode ser negativo.")
        robot.units_separated = units
        self._db.add(robot)
        self._db.commit()
        self._db.refresh(robot)
        return self._to_detail(robot)

    def delete_robot(self, robot_id: int) -> bool:
        robot = self._repo.get_by_id(robot_id)
        if robot is None:
            return False
        if robot.current_order_id:
            order = robot.current_order
            if order is not None and order.status == ServiceOrderStatus.IN_PROGRESS.value:
                order.status = ServiceOrderStatus.PENDING.value
                self._db.add(order)
        self._db.delete(robot)
        self._db.commit()
        return True

    @staticmethod
    def _to_summary(robot: Robot) -> RobotSummary:
        os_code = robot.current_order.os_code if robot.current_order else None
        return RobotSummary(
            id=robot.id,
            code=robot.code,
            name=robot.name,
            location=robot.location or "",
            model=robot.model,
            status=robot.status,
            online=is_robot_online(robot.status),
            current_os_code=os_code,
        )

    @staticmethod
    def _to_detail(robot: Robot) -> RobotDetail:
        elapsed: int | None = None
        if robot.job_started_at:
            start = robot.job_started_at
            if start.tzinfo is None:
                start = start.replace(tzinfo=UTC)
            elapsed = max(0, int((datetime.now(UTC) - start).total_seconds()))

        brief: ServiceOrderBrief | None = None
        if robot.current_order:
            brief = ServiceOrderBrief.model_validate(robot.current_order)

        return RobotDetail(
            id=robot.id,
            code=robot.code,
            name=robot.name,
            location=robot.location or "",
            model=robot.model,
            specifications=robot.specifications,
            max_units_per_hour=robot.max_units_per_hour,
            status=robot.status,
            online=is_robot_online(robot.status),
            units_separated=robot.units_separated,
            job_started_at=robot.job_started_at,
            elapsed_seconds=elapsed,
            current_order=brief,
        )
