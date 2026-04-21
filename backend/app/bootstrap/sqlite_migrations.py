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
    if "total_pause_seconds" not in so_cols:
        conn.execute(text("ALTER TABLE service_orders ADD COLUMN total_pause_seconds INTEGER"))

    user_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()}
    if "is_admin" not in user_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"))

    _cleanup_orphan_robot_refs(conn)
    _ensure_robots_autoincrement(conn)


def _cleanup_orphan_robot_refs(conn: Connection) -> None:
    """Zera vínculos em service_orders que apontam para robôs já excluídos OU para ids reciclados.

    Dois cenários corrigidos:
    1. id inexistente: sem FK materializada (ON DELETE SET NULL), deleções antigas deixaram
       ids inválidos em completed_by_robot_id / cancelled_by_robot_id.
    2. id reciclado: se o SQLite reciclou um id num novo separador, OS cujo evento
       (completed_at / cancelled_at) é anterior a robots.created_at não podem ter sido
       processadas pelo separador atual — são sobras do antigo e precisam ser desvinculadas.
    """
    conn.execute(
        text(
            """
            UPDATE service_orders
               SET completed_by_robot_id = NULL
             WHERE completed_by_robot_id IS NOT NULL
               AND completed_by_robot_id NOT IN (SELECT id FROM robots)
            """
        )
    )
    conn.execute(
        text(
            """
            UPDATE service_orders
               SET cancelled_by_robot_id = NULL
             WHERE cancelled_by_robot_id IS NOT NULL
               AND cancelled_by_robot_id NOT IN (SELECT id FROM robots)
            """
        )
    )
    conn.execute(
        text(
            """
            UPDATE service_orders
               SET completed_by_robot_id = NULL
             WHERE completed_by_robot_id IS NOT NULL
               AND completed_at IS NOT NULL
               AND completed_at < (
                   SELECT r.created_at FROM robots r WHERE r.id = service_orders.completed_by_robot_id
               )
            """
        )
    )
    conn.execute(
        text(
            """
            UPDATE service_orders
               SET cancelled_by_robot_id = NULL
             WHERE cancelled_by_robot_id IS NOT NULL
               AND cancelled_at IS NOT NULL
               AND cancelled_at < (
                   SELECT r.created_at FROM robots r WHERE r.id = service_orders.cancelled_by_robot_id
               )
            """
        )
    )


def _ensure_robots_autoincrement(conn: Connection) -> None:
    """Garante AUTOINCREMENT em robots.id para que ids de separadores excluídos não sejam reciclados.

    Sem AUTOINCREMENT, SQLite usa MAX(id)+1: ao excluir o último robô e criar outro,
    o novo recebe o id antigo — e qualquer referência residual passa a apontar para ele.
    """
    row = conn.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='robots'")
    ).fetchone()
    if row is None:
        return
    ddl = (row[0] or "").upper()
    if "AUTOINCREMENT" in ddl:
        return

    # Recria tabela com AUTOINCREMENT preservando dados; FKs são desligadas apenas durante a cópia.
    conn.execute(text("PRAGMA foreign_keys=OFF"))
    try:
        conn.execute(
            text(
                """
                CREATE TABLE robots__new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(32) NOT NULL,
                    name VARCHAR(128) NOT NULL,
                    location VARCHAR(256) NOT NULL DEFAULT '',
                    model VARCHAR(128) NOT NULL,
                    specifications TEXT NOT NULL DEFAULT '',
                    max_units_per_hour INTEGER NOT NULL DEFAULT 500,
                    status VARCHAR(32) NOT NULL DEFAULT 'offline',
                    current_order_id INTEGER,
                    job_started_at DATETIME,
                    paused_at DATETIME,
                    elapsed_pause_seconds INTEGER NOT NULL DEFAULT 0,
                    units_separated INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
                    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
                    FOREIGN KEY(current_order_id) REFERENCES service_orders(id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO robots__new (
                    id, code, name, location, model, specifications, max_units_per_hour, status,
                    current_order_id, job_started_at, paused_at, elapsed_pause_seconds,
                    units_separated, created_at, updated_at
                )
                SELECT id, code, name, COALESCE(location,''), model, COALESCE(specifications,''),
                       COALESCE(max_units_per_hour, 500), COALESCE(status, 'offline'),
                       current_order_id, job_started_at, paused_at,
                       COALESCE(elapsed_pause_seconds, 0), COALESCE(units_separated, 0),
                       COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP)
                  FROM robots
                """
            )
        )
        # Mantém o contador acima do maior id existente para que próximos ids nunca colidam.
        max_id_row = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM robots__new")).fetchone()
        max_id = int(max_id_row[0]) if max_id_row else 0
        conn.execute(
            text(
                "INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('robots__new', :v)"
            ),
            {"v": max_id},
        )
        conn.execute(text("DROP TABLE robots"))
        conn.execute(text("ALTER TABLE robots__new RENAME TO robots"))
        # O RENAME move o registro em sqlite_sequence automaticamente.
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_robots_code ON robots(code)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_robots_status ON robots(status)"))
    finally:
        conn.execute(text("PRAGMA foreign_keys=ON"))
