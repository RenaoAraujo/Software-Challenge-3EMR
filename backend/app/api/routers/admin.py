from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database, limit_sensitive, require_admin, require_csrf_token
from app.models.entities import User
from app.schemas.audit import AuditLogListOut, AuditLogOut, AuditLogsClearOut
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin")


@router.get("/audit-logs", response_model=AuditLogListOut)
def list_audit_logs(
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    username: str | None = Query(
        None,
        max_length=64,
        description="Filtra por nome de usuário (contém, sem distinguir maiúsculas/minúsculas).",
    ),
    de: date | None = Query(
        None,
        description="Início do intervalo de datas do registro (AAAA-MM-DD, inclusivo, UTC).",
    ),
    ate: date | None = Query(
        None,
        description="Fim do intervalo (AAAA-MM-DD, inclusivo, UTC). Use com `de` ou sozinho.",
    ),
    category: str | None = Query(
        None,
        max_length=32,
        description=(
            "Grupo: historico, cancelamento, pausa, retomada, conclusao, inicio_os, "
            "sessao, admin, os_todas."
        ),
    ),
    db: Session = Depends(get_database),
    admin: User = Depends(require_admin),
) -> AuditLogListOut:
    has_filters = bool(
        (username or "").strip()
        or (category or "").strip()
        or de is not None
        or ate is not None
    )
    if offset == 0 and not has_filters:
        AuditService(db).log(
            user_id=admin.id,
            username=admin.username,
            action="view_logs",
            description="Abriu ou atualizou a lista de logs de auditoria.",
        )
    try:
        rows, total = AuditService(db).list_filtered(
            limit=limit,
            offset=offset,
            username_contains=username,
            category=category,
            de=de,
            ate=ate,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    items = [
        AuditLogOut(
            id=r.id,
            user_id=r.user_id,
            username=r.username,
            action=r.action,
            description=r.description,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return AuditLogListOut(items=items, total=total)


@router.delete("/audit-logs", response_model=AuditLogsClearOut)
def clear_audit_logs(
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
    __: None = Depends(require_csrf_token),
    ___: None = Depends(limit_sensitive),
) -> AuditLogsClearOut:
    deleted = AuditService(db).clear_all()
    return AuditLogsClearOut(deleted=deleted)
