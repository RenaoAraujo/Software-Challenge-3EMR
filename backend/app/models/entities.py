from __future__ import annotations

import enum
import json
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RobotStatus(str, enum.Enum):
    """offline = cadastrado / sem conexão operacional; idle = online e ocioso; running = em OS."""

    OFFLINE = "offline"
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    MAINTENANCE = "maintenance"


def is_robot_online(status: str) -> bool:
    """Online: ocioso ou em operação. Offline: sem conexão, manutenção ou erro."""
    return status in (RobotStatus.IDLE.value, RobotStatus.RUNNING.value)


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
