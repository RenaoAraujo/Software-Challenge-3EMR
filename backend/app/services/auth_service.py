from sqlalchemy import select
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.entities import User

# pbkdf2_sha256 evita dependência frágil do bcrypt em alguns ambientes Windows.
_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto", pbkdf2_sha256__default_rounds=290_000)


class AuthService:
    def __init__(self, db: Session) -> None:
        self._db = db

    @staticmethod
    def hash_password(plain: str) -> str:
        return _pwd.hash(plain)

    def verify_credentials(self, username: str, password: str) -> User | None:
        uname = (username or "").strip().lower()
        if not uname:
            return None
        user = self._db.scalar(select(User).where(User.username == uname))
        if user is None:
            return None
        if not _pwd.verify(password, user.password_hash):
            return None
        return user
