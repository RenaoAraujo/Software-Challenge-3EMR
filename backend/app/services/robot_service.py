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
            if (
                robot.status in (RobotStatus.RUNNING.value, RobotStatus.PAUSED.value)
                and robot.current_order_id
            ):
                raise ValueError("Não altere o status enquanto houver OS em execução ou pausada.")
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

    def _apply_order_completion(self, robot: Robot) -> None:
        """Persiste conclusão da OS atual usando units_separated já definido no robô."""
        order = robot.current_order
        if order is None:
            raise ValueError("Ordem vinculada não encontrada.")
        now = datetime.now(UTC)
        order.status = ServiceOrderStatus.COMPLETED.value
        order.completed_at = now
        order.completed_by_robot_id = robot.id
        order.completed_units = max(0, int(robot.units_separated))
        robot.current_order_id = None
        robot.job_started_at = None
        robot.paused_at = None
        robot.elapsed_pause_seconds = 0
        robot.units_separated = 0
        robot.status = RobotStatus.IDLE.value
        self._db.add(robot)
        self._db.add(order)

    def update_units_separated(
        self, robot_id: int, units: int
    ) -> tuple[RobotDetail | None, str | None]:
        """Retorna (detalhe, código da OS) se a OS foi concluída automaticamente ao atingir a meta; senão (_, None)."""
        robot = self._repo.get_by_id(robot_id)
        if robot is None:
            return None, None
        if robot.status != RobotStatus.RUNNING.value:
            raise ValueError(
                "Só é possível registrar unidades com o separador em execução (não pausado)."
            )
        if units < 0:
            raise ValueError("units_separated não pode ser negativo.")
        robot.units_separated = units
        order = robot.current_order
        expected = int(order.expected_units) if order is not None else 0
        completed_os_code: str | None = None
        if order is not None and expected > 0 and units >= expected:
            completed_os_code = order.os_code
            self._apply_order_completion(robot)
        else:
            self._db.add(robot)
        self._db.commit()
        self._db.refresh(robot)
        full = self._repo.get_by_id(robot_id)
        assert full is not None
        return self._to_detail(full), completed_os_code

    def complete_current_order(self, robot_id: int) -> RobotDetail | None:
        """Marca a OS atual como concluída e registra unidades para o histórico."""
        robot = self._repo.get_by_id(robot_id)
        if robot is None:
            return None
        if robot.current_order_id is None:
            raise ValueError("Não há ordem em execução para concluir neste separador.")
        if robot.status not in (RobotStatus.RUNNING.value, RobotStatus.PAUSED.value):
            raise ValueError("Não há ordem em execução para concluir neste separador.")
        if robot.current_order is None:
            raise ValueError("Ordem vinculada não encontrada.")
        self._apply_order_completion(robot)
        self._db.commit()
        self._db.refresh(robot)
        full = self._repo.get_by_id(robot_id)
        assert full is not None
        return self._to_detail(full)

    def cancel_current_order(self, robot_id: int) -> RobotDetail | None:
        """Interrompe a OS no separador: libera o robô e marca a OS como cancelada (histórico)."""
        robot = self._repo.get_by_id(robot_id)
        if robot is None:
            return None
        if robot.current_order_id is None:
            raise ValueError("Não há ordem vinculada a este separador.")
        if robot.status not in (RobotStatus.RUNNING.value, RobotStatus.PAUSED.value):
            raise ValueError("Só é possível cancelar a OS enquanto o separador está em execução ou pausado.")
        order = robot.current_order
        now = datetime.now(UTC)
        if order is not None:
            order.status = ServiceOrderStatus.CANCELLED.value
            order.cancelled_at = now
            order.cancelled_by_robot_id = robot_id
            order.assigned_at = None
            order.completed_at = None
            order.completed_by_robot_id = None
            order.completed_units = None
            self._db.add(order)
        robot.current_order_id = None
        robot.job_started_at = None
        robot.paused_at = None
        robot.elapsed_pause_seconds = 0
        robot.units_separated = 0
        robot.status = RobotStatus.IDLE.value
        self._db.add(robot)
        self._db.commit()
        self._db.refresh(robot)
        full = self._repo.get_by_id(robot_id)
        assert full is not None
        return self._to_detail(full)

    def pause_separation(self, robot_id: int) -> RobotDetail | None:
        """Pausa a OS: congela o tempo decorrido até retomar."""
        robot = self._repo.get_by_id(robot_id)
        if robot is None:
            return None
        if robot.status != RobotStatus.RUNNING.value or robot.current_order_id is None:
            raise ValueError("Só é possível pausar com uma OS em execução.")
        now = datetime.now(UTC)
        robot.status = RobotStatus.PAUSED.value
        robot.paused_at = now
        ord_ = robot.current_order
        if ord_ is not None:
            ord_.pause_count = int(ord_.pause_count or 0) + 1
            self._db.add(ord_)
        self._db.add(robot)
        self._db.commit()
        self._db.refresh(robot)
        full = self._repo.get_by_id(robot_id)
        assert full is not None
        return self._to_detail(full)

    def resume_separation(self, robot_id: int) -> RobotDetail | None:
        """Retoma a OS após pausa."""
        robot = self._repo.get_by_id(robot_id)
        if robot is None:
            return None
        if robot.status != RobotStatus.PAUSED.value:
            raise ValueError("O separador não está pausado.")
        now = datetime.now(UTC)
        if robot.paused_at is not None:
            p = robot.paused_at
            if p.tzinfo is None:
                p = p.replace(tzinfo=UTC)
            segment = int((now - p).total_seconds())
            robot.elapsed_pause_seconds = max(0, int(robot.elapsed_pause_seconds or 0)) + max(0, segment)
        robot.paused_at = None
        robot.status = RobotStatus.RUNNING.value
        self._db.add(robot)
        self._db.commit()
        self._db.refresh(robot)
        full = self._repo.get_by_id(robot_id)
        assert full is not None
        return self._to_detail(full)

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
        order = robot.current_order
        os_code = order.os_code if order else None
        expected = int(order.expected_units) if order else None
        client_raw = (order.client_name or "").strip() if order else ""
        client = client_raw or None
        elapsed: int | None = None
        if (
            order is not None
            and robot.job_started_at is not None
            and robot.status in (RobotStatus.RUNNING.value, RobotStatus.PAUSED.value)
        ):
            elapsed = RobotService._effective_elapsed_seconds(robot)
        return RobotSummary(
            id=robot.id,
            code=robot.code,
            name=robot.name,
            location=robot.location or "",
            model=robot.model,
            status=robot.status,
            online=is_robot_online(robot.status),
            current_os_code=os_code,
            units_separated=int(robot.units_separated or 0),
            expected_units=expected,
            client_name=client,
            elapsed_seconds=elapsed,
        )

    @staticmethod
    def _effective_elapsed_seconds(robot: Robot) -> int | None:
        if robot.job_started_at is None:
            return None
        now = datetime.now(UTC)
        start = robot.job_started_at
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        wall = (now - start).total_seconds()
        ep = max(0, int(robot.elapsed_pause_seconds or 0))
        current_pause = 0.0
        if robot.paused_at is not None:
            p = robot.paused_at
            if p.tzinfo is None:
                p = p.replace(tzinfo=UTC)
            current_pause = max(0.0, (now - p).total_seconds())
        return max(0, int(wall - ep - current_pause))

    @staticmethod
    def _to_detail(robot: Robot) -> RobotDetail:
        elapsed: int | None = RobotService._effective_elapsed_seconds(robot)

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
