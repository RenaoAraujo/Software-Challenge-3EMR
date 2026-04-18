from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import User
from app.security.csrf import validate_csrf_token
from app.security.rate_limit import check_rate_limit


def get_database() -> Generator[Session, None, None]:
    yield from get_db()


def require_auth(request: Request) -> None:
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Autenticação necessária.")


def get_current_user(request: Request, db: Session = Depends(get_database)) -> User:
    raw = request.session.get("user")
    if not raw or raw.get("id") is None:
        raise HTTPException(status_code=401, detail="Autenticação necessária.")
    user = db.get(User, int(raw["id"]))
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Sessão inválida.")
    return user


def require_admin(request: Request, db: Session = Depends(get_database)) -> User:
    raw = request.session.get("user")
    if not raw or raw.get("id") is None:
        raise HTTPException(status_code=401, detail="Autenticação necessária.")
    user = db.get(User, int(raw["id"]))
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Sessão inválida.")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return user


def require_csrf_token(x_csrf_token: str | None = Header(None, alias="X-CSRF-Token")) -> None:
    if not x_csrf_token or not validate_csrf_token(x_csrf_token):
        raise HTTPException(
            status_code=403,
            detail="Token de segurança (CSRF) ausente ou inválido. Atualize a página.",
        )


def limit_sensitive(request: Request) -> None:
    check_rate_limit(request)
