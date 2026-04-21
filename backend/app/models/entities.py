from __future__ import annotations

import enum
import json
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RobotStatus(str, enum.Enum):
    """offline = cadastrado / sem conexão operacional; idle = online e ocioso; running = em OS."""

    OFFLINE = "offline"
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"


def is_robot_online(status: str) -> bool:
    """Online: ocioso, em operação ou pausado. Offline: sem conexão, manutenção ou erro."""
    return status in (RobotStatus.IDLE.value, RobotStatus.RUNNING.value, RobotStatus.PAUSED.value)


class ServiceOrderStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Robot(Base):
    __tablename__ = "robots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    location: Mapped[str] = mapped_column(String(256), default="")
    model: Mapped[str] = mapped_column(String(128))
    specifications: Mapped[str] = mapped_column(Text, default="")
    max_units_per_hour: Mapped[int] = mapped_column(Integer, default=500)
    status: Mapped[str] = mapped_column(String(32), default=RobotStatus.OFFLINE.value, index=True)

    current_order_id: Mapped[int | None] = mapped_column(ForeignKey("service_orders.id"), nullable=True)
    job_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    elapsed_pause_seconds: Mapped[int] = mapped_column(Integer, default=0)
    units_separated: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    current_order: Mapped[ServiceOrder | None] = relationship(
        "ServiceOrder",
        foreign_keys=[current_order_id],
    )


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    os_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    client_name: Mapped[str] = mapped_column(String(256), default="")
    expected_units: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default=ServiceOrderStatus.PENDING.value)
    medicines_json: Mapped[str] = mapped_column(Text, default="[]")

    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed_by_robot_id: Mapped[int | None] = mapped_column(
        ForeignKey("robots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Nome do separador na conclusão; permanece no histórico se o robô for excluído (FK zera só o id).
    completed_by_robot_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    completed_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    cancelled_by_robot_id: Mapped[int | None] = mapped_column(
        ForeignKey("robots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cancelled_by_robot_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cancelled_separated_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cancelled_avg_seconds_per_unit: Mapped[float | None] = mapped_column(Float, nullable=True)
    cancel_error_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Duração total (atribuição → cancelamento), em segundos; gravada no cancelamento antes de limpar assigned_at.
    cancelled_wall_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Soma dos segundos em pausa durante a execução (gravada ao concluir ou cancelar).
    total_pause_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    @property
    def medicines(self) -> list[str]:
        """Lista de medicamentos a separar (persistidos como JSON no campo medicines_json)."""
        try:
            data = json.loads(self.medicines_json or "[]")
            if not isinstance(data, list):
                return []
            return [str(x).strip() for x in data if str(x).strip()]
        except json.JSONDecodeError:
            return []


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    username: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
