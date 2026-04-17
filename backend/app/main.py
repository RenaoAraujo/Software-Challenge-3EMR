from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.bootstrap.seed import seed_if_empty
from app.bootstrap.sqlite_migrations import apply_sqlite_migrations
from app.config import settings
from app.database import SessionLocal, engine
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.models.base import Base


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        apply_sqlite_migrations(conn)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="EMR — Facilitador de separação",
        description="Painel para ordens de serviço e integração com robôs de separação.",
        lifespan=lifespan,
        version="1.0.0",
    )
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix="/api")

    app_dir = Path(__file__).resolve().parent
    img_dir = app_dir / "img"
    if img_dir.is_dir():
        application.mount("/img", StaticFiles(directory=str(img_dir)), name="img")

    backend_dir = Path(__file__).resolve().parent.parent
    frontend_dir = backend_dir.parent / "frontend"
    if frontend_dir.is_dir():
        application.mount(
            "/",
            StaticFiles(directory=str(frontend_dir), html=True),
            name="site",
        )
    return application


app = create_app()
