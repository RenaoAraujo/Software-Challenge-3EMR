from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.schemas.notifications import OsCompletionFeedOut, OsCompletionNotificationItem
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications")


@router.get("/os-completions", response_model=OsCompletionFeedOut)
def os_completion_feed(
    limit: int = Query(40, ge=1, le=100),
    db: Session = Depends(get_database),
) -> OsCompletionFeedOut:
    """Lista conclusões de OS registradas em auditoria — mesma fonte para todos os usuários."""
    rows = NotificationService(db).list_os_completion_events(limit=limit)
    items = [
        OsCompletionNotificationItem(
            id=r.id,
            created_at=r.created_at,
            description=r.description or "",
            username=r.username or "—",
        )
        for r in rows
    ]
    return OsCompletionFeedOut(items=items)
