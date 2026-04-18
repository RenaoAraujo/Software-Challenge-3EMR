from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_database, limit_sensitive
from app.models.entities import User
from app.schemas.auth import LoginBody, UserSessionOut
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
