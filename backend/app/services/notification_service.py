from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AuditLog

_OS_COMPLETION_ACTIONS = frozenset({"os_completed", "os_completed_auto"})


class NotificationService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_os_completion_events(self, *, limit: int = 40) -> list[AuditLog]:
        limit = max(1, min(limit, 100))
        stmt = (
            select(AuditLog)
            .where(AuditLog.action.in_(_OS_COMPLETION_ACTIONS))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(self._db.scalars(stmt).all())
