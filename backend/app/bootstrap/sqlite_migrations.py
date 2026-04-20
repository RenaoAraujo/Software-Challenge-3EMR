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
    if "paused_at" not in col_names:
        conn.execute(text("ALTER TABLE robots ADD COLUMN paused_at DATETIME"))
    if "elapsed_pause_seconds" not in col_names:
        conn.execute(text("ALTER TABLE robots ADD COLUMN elapsed_pause_seconds INTEGER NOT NULL DEFAULT 0"))

    so_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(service_orders)")).fetchall()}
    if "client_name" not in so_cols:
        conn.execute(
            text("ALTER TABLE service_orders ADD COLUMN client_name VARCHAR(256) NOT NULL DEFAULT ''")
        )
    if "medicines_json" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN medicines_json TEXT NOT NULL DEFAULT '[]'"))
    if "completed_at" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN completed_at DATETIME"))
    if "completed_by_robot_id" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN completed_by_robot_id INTEGER"))
    if "completed_units" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN completed_units INTEGER"))
    if "assigned_at" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN assigned_at DATETIME"))
    if "pause_count" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN pause_count INTEGER NOT NULL DEFAULT 0"))
    if "cancelled_at" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN cancelled_at DATETIME"))
    if "cancelled_by_robot_id" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN cancelled_by_robot_id INTEGER"))
    if "completed_by_robot_name" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN completed_by_robot_name VARCHAR(128)"))
    if "cancelled_by_robot_name" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN cancelled_by_robot_name VARCHAR(128)"))
    if "cancelled_separated_units" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN cancelled_separated_units INTEGER"))
    if "cancelled_avg_seconds_per_unit" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN cancelled_avg_seconds_per_unit REAL"))
    if "cancel_error_description" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN cancel_error_description TEXT"))
    if "cancel_error_code" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN cancel_error_code VARCHAR(64)"))
    if "cancelled_wall_seconds" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN cancelled_wall_seconds INTEGER"))

    user_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()}
    if "is_admin" not in user_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"))
