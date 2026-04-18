"""Auditoria ligada à sessão do usuário (rotas autenticadas)."""

from fastapi import Request
from sqlalchemy.orm import Session

from app.services.audit_service import AuditService


def audit_session_action(request: Request, db: Session, *, action: str, description: str) -> None:
    raw = request.session.get("user")
    if not raw:
        return
    AuditService(db).log(
        user_id=raw.get("id"),
        username=str(raw.get("username", "")),
        action=action,
        description=description,
    )
