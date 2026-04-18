from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_database, limit_sensitive, require_admin, require_csrf_token
from app.models.entities import User
from app.schemas.audit import AuditLogListOut, AuditLogOut, AuditLogsClearOut
from app.schemas.user import AdminUpdateUserBody, CreateUserBody, UserListOut, UserSummaryOut
from app.services.audit_service import AuditService
from app.services.user_admin_service import admin_update_user, create_user, list_users_ordered

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
            "sessao, contas, os_todas."
        ),
    ),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> AuditLogListOut:
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


@router.get("/users", response_model=UserListOut)
def admin_list_users(
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> UserListOut:
    rows = list_users_ordered(db)
    return UserListOut(
        users=[UserSummaryOut(id=u.id, username=u.username, is_admin=bool(u.is_admin)) for u in rows]
    )


@router.post("/users", response_model=UserSummaryOut)
def admin_create_user(
    body: CreateUserBody,
    db: Session = Depends(get_database),
    admin: User = Depends(require_admin),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> UserSummaryOut:
    try:
        u = create_user(
            db,
            username=body.username,
            password=body.password,
            is_admin=body.is_admin,
        )
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Nome de usuário já existe.") from None
    AuditService(db).log(
        user_id=admin.id,
        username=admin.username,
        action="user_created",
        description=f'Cadastrou o usuário "{u.username}" (admin={"sim" if u.is_admin else "não"}).',
    )
    return UserSummaryOut(id=u.id, username=u.username, is_admin=bool(u.is_admin))


@router.patch("/users/{user_id}", response_model=UserSummaryOut)
def admin_patch_user(
    user_id: int,
    body: AdminUpdateUserBody,
    db: Session = Depends(get_database),
    admin: User = Depends(require_admin),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> UserSummaryOut:
    before = db.get(User, user_id)
    if before is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    try:
        u = admin_update_user(
            db,
            target_id=user_id,
            new_password=body.new_password,
            is_admin=body.is_admin,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    audit = AuditService(db)
    if body.new_password is not None:
        audit.log(
            user_id=admin.id,
            username=admin.username,
            action="password_changed_by_admin",
            description=f'Alterou a senha do usuário "{u.username}".',
        )
    if body.is_admin is not None and before.is_admin != u.is_admin:
        if u.is_admin:
            audit.log(
                user_id=admin.id,
                username=admin.username,
                action="user_promoted_admin",
                description=f'Promoveu "{u.username}" a administrador.',
            )
        else:
            audit.log(
                user_id=admin.id,
                username=admin.username,
                action="user_demoted_admin",
                description=f'Removeu o perfil de administrador de "{u.username}".',
            )
    return UserSummaryOut(id=u.id, username=u.username, is_admin=bool(u.is_admin))
