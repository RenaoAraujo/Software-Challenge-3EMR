"""Migrações leves para SQLite (sem Alembic)."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.config import settings


def apply_sqlite_migrations(conn: Connection) -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    rows = conn.execute(text("PRAGMA table_info(robots)")).fetchall()
    col_names = {row[1] for row in rows}
    if "location" not in col_names:
        conn.execute(
            text("ALTER TABLE robots ADD COLUMN location VARCHAR(256) NOT NULL DEFAULT ''")
        )

    so_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(service_orders)")).fetchall()}
    if "client_name" not in so_cols:
        conn.execute(
            text("ALTER TABLE service_orders ADD COLUMN client_name VARCHAR(256) NOT NULL DEFAULT ''")
        )
    if "medicines_json" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN medicines_json TEXT NOT NULL DEFAULT '[]'"))
