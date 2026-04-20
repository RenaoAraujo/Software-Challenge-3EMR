from datetime import datetime

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import Robot, ServiceOrder, ServiceOrderStatus


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

    def list_ended_orders_report(
        self,
        *,
        start_utc: datetime | None,
        end_utc_exclusive: datetime | None,
        limit: int,
        offset: int,
        situacao: str | None = None,
        os_contains: str | None = None,
        nome_cliente_contains: str | None = None,
        cliente_contains: str | None = None,
        nome_separador_contains: str | None = None,
        codigo_separador_contains: str | None = None,
        restrict_ids: list[int] | None = None,
    ) -> tuple[list[ServiceOrder], int]:
        """OS concluídas ou canceladas (com data de evento); mais recentes primeiro."""
        completed_cond = and_(
            ServiceOrder.status == ServiceOrderStatus.COMPLETED.value,
            ServiceOrder.completed_at.is_not(None),
        )
        cancelled_cond = and_(
            ServiceOrder.status == ServiceOrderStatus.CANCELLED.value,
            ServiceOrder.cancelled_at.is_not(None),
        )
        if start_utc is not None and end_utc_exclusive is not None:
            completed_cond = and_(
                completed_cond,
                ServiceOrder.completed_at >= start_utc,
                ServiceOrder.completed_at < end_utc_exclusive,
            )
            cancelled_cond = and_(
                cancelled_cond,
                ServiceOrder.cancelled_at >= start_utc,
                ServiceOrder.cancelled_at < end_utc_exclusive,
            )
        if situacao == "concluida":
            base = completed_cond
        elif situacao == "cancelada":
            base = cancelled_cond
        else:
            base = or_(completed_cond, cancelled_cond)

        if os_contains and os_contains.strip():
            pat = f"%{os_contains.strip()}%"
            base = and_(base, ServiceOrder.os_code.ilike(pat))
        nc = (nome_cliente_contains or "").strip()
        cl = (cliente_contains or "").strip()
        if nc or cl:
            if nc and cl:
                base = and_(
                    base,
                    or_(
                        ServiceOrder.client_name.ilike(f"%{nc}%"),
                        ServiceOrder.client_name.ilike(f"%{cl}%"),
                    ),
                )
            elif nc:
                base = and_(base, ServiceOrder.client_name.ilike(f"%{nc}%"))
            else:
                base = and_(base, ServiceOrder.client_name.ilike(f"%{cl}%"))
        if nome_separador_contains and nome_separador_contains.strip():
            pat = f"%{nome_separador_contains.strip()}%"
            sep_nome = or_(
                ServiceOrder.completed_by_robot_name.ilike(pat),
                ServiceOrder.cancelled_by_robot_name.ilike(pat),
                exists(
                    select(1)
                    .select_from(Robot)
                    .where(
                        Robot.id == ServiceOrder.completed_by_robot_id,
                        Robot.name.ilike(pat),
                    )
                ),
                exists(
                    select(1)
                    .select_from(Robot)
                    .where(
                        Robot.id == ServiceOrder.cancelled_by_robot_id,
                        Robot.name.ilike(pat),
                    )
                ),
            )
            base = and_(base, sep_nome)
        if codigo_separador_contains and codigo_separador_contains.strip():
            pat = f"%{codigo_separador_contains.strip()}%"
            sep_cod = or_(
                exists(
                    select(1)
                    .select_from(Robot)
                    .where(
                        Robot.id == ServiceOrder.completed_by_robot_id,
                        Robot.code.ilike(pat),
                    )
                ),
                exists(
                    select(1)
                    .select_from(Robot)
                    .where(
                        Robot.id == ServiceOrder.cancelled_by_robot_id,
                        Robot.code.ilike(pat),
                    )
                ),
            )
            base = and_(base, sep_cod)

        if restrict_ids is not None and len(restrict_ids) > 0:
            base = and_(base, ServiceOrder.id.in_(tuple(restrict_ids)))

        sort_col = case(
            (ServiceOrder.status == ServiceOrderStatus.COMPLETED.value, ServiceOrder.completed_at),
            else_=ServiceOrder.cancelled_at,
        )
        count_stmt = select(func.count()).select_from(ServiceOrder).where(base)
        total = int(self._db.scalar(count_stmt) or 0)
        stmt = (
            select(ServiceOrder)
            .where(base)
            .order_by(sort_col.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = list(self._db.scalars(stmt).all())
        return rows, total
