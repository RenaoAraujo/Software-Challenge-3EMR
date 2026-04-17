from collections.abc import Generator

from fastapi import Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.csrf import validate_csrf_token
from app.security.rate_limit import check_rate_limit


def get_database() -> Generator[Session, None, None]:
    yield from get_db()


def require_csrf_token(x_csrf_token: str | None = Header(None, alias="X-CSRF-Token")) -> None:
    if not x_csrf_token or not validate_csrf_token(x_csrf_token):
        raise HTTPException(
            status_code=403,
            detail="Token de segurança (CSRF) ausente ou inválido. Atualize a página.",
        )


def limit_sensitive(request: Request) -> None:
    check_rate_limit(request)
