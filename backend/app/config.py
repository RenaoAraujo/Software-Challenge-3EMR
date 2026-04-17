from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Sempre `backend/data/emr.db`, independente do diretório de onde o uvicorn foi iniciado.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_SQLITE_PATH = (_BACKEND_DIR / "data" / "emr.db").resolve()
DEFAULT_DATABASE_URL = f"sqlite:///{_DEFAULT_SQLITE_PATH.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EMR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(default=DEFAULT_DATABASE_URL)
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    cors_origins: str = (
        "http://127.0.0.1:8765,http://localhost:8765,"
        "http://127.0.0.1:8000,http://localhost:8000"
    )
    environment: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def ensure_sqlite_parent_dir(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    path = Path(url.replace("sqlite:///", "", 1))
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
