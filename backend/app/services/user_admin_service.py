from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import User
from app.services.auth_service import AuthService


def list_users_ordered(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.username.asc())).all())


def create_user(db: Session, *, username: str, password: str, is_admin: bool) -> User:
    uname = (username or "").strip().lower()
    u = User(username=uname, password_hash=AuthService.hash_password(password), is_admin=is_admin)
    db.add(u)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(u)
    return u


def admin_update_user(
    db: Session,
    *,
    target_id: int,
    new_password: str | None,
    is_admin: bool | None,
) -> User:
    target = db.get(User, target_id)
    if target is None:
        raise ValueError("Usuário não encontrado.")

    if is_admin is False and target.is_admin:
        cnt = db.scalar(select(func.count()).select_from(User).where(User.is_admin.is_(True)))
        if (cnt or 0) <= 1:
            raise ValueError("Não é possível remover o último administrador.")

    if new_password is not None:
        target.password_hash = AuthService.hash_password(new_password)

    if is_admin is not None:
        target.is_admin = is_admin

    db.add(target)
    db.commit()
    db.refresh(target)
    return target
