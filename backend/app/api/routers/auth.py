from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_database, limit_sensitive, require_csrf_token
from app.models.entities import User
from app.schemas.auth import LoginBody, UserSessionOut
from app.schemas.user import ChangePasswordBody
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


@router.post("/login")
def login(
    request: Request,
    body: LoginBody,
    db: Session = Depends(get_database),
    _: None = Depends(limit_sensitive),
) -> dict:
    svc = AuthService(db)
    user = svc.verify_credentials(body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
    payload = UserSessionOut(id=user.id, username=user.username, is_admin=bool(user.is_admin))
    request.session["user"] = payload.model_dump()
    AuditService(db).log(
        user_id=user.id,
        username=user.username,
        action="login",
        description="Autenticou-se no sistema.",
    )
    return {"user": payload.model_dump()}


@router.post("/logout", status_code=204)
def logout(request: Request, db: Session = Depends(get_database)) -> Response:
    raw = request.session.get("user")
    if raw:
        AuditService(db).log(
            user_id=raw.get("id"),
            username=str(raw.get("username", "")),
            action="logout",
            description="Encerrou sessão.",
        )
    request.session.clear()
    return Response(status_code=204)


@router.patch("/me/password")
def change_own_password(
    body: ChangePasswordBody,
    request: Request,
    db: Session = Depends(get_database),
    user: User = Depends(get_current_user),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> dict:
    if not AuthService.verify_password(user, body.current_password):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    user.password_hash = AuthService.hash_password(body.new_password)
    db.add(user)
    db.commit()
    AuditService(db).log(
        user_id=user.id,
        username=user.username,
        action="password_changed_self",
        description="Alterou a própria senha de acesso.",
    )
    return {"ok": True}


@router.get("/me")
def auth_me(request: Request, db: Session = Depends(get_database)) -> dict:
    raw = request.session.get("user")
    if not raw:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    user = db.get(User, int(raw["id"]))
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    payload = UserSessionOut(id=user.id, username=user.username, is_admin=bool(user.is_admin))
    request.session["user"] = payload.model_dump()
    return {"user": payload.model_dump()}
