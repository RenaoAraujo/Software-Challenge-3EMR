from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Robot


class RobotRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self, name_contains: str | None = None) -> list[Robot]:
        stmt = (
            select(Robot)
            .options(joinedload(Robot.current_order))
            .order_by(Robot.code)
        )
        if name_contains is not None:
            q = name_contains.strip()
            if q:
                stmt = stmt.where(Robot.name.ilike(f"%{q}%"))
        return list(self._db.scalars(stmt).unique().all())

    def get_by_id(self, robot_id: int) -> Robot | None:
        stmt = (
            select(Robot)
            .options(joinedload(Robot.current_order))
            .where(Robot.id == robot_id)
        )
        return self._db.scalars(stmt).unique().first()

    def get_by_code(self, code: str, *, exclude_id: int | None = None) -> Robot | None:
        stmt = select(Robot).where(Robot.code == code)
        if exclude_id is not None:
            stmt = stmt.where(Robot.id != exclude_id)
        return self._db.scalars(stmt).first()
