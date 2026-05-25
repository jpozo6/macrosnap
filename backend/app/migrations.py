"""Migraciones in-place idempotentes ejecutadas al arrancar la app.

El proyecto todavía no usa Alembic (ver `migrations/README.md`) y se apoya en
`Base.metadata.create_all(bind=engine)` para crear el schema. `create_all` no
añade columnas a tablas ya existentes, así que cuando se mergea una feature
que añade columnas al modelo (p. ej. el flujo de reset de contraseña en
`2288fc6`), las bases de datos en producción se quedan desincronizadas y los
endpoints fallan con 500 `UndefinedColumn`.

Este módulo aplica los `ALTER TABLE ADD COLUMN` necesarios de forma idempotente
en cada arranque. Sustituirlo por Alembic cuando crezca la base de usuarios.
"""

from __future__ import annotations

import logging

from sqlalchemy import Engine, inspect, text

logger = logging.getLogger(__name__)


def _timestamp_type(dialect_name: str) -> str:
    # Postgres usa TIMESTAMP; SQLite acepta DATETIME (afinidad textual).
    return "TIMESTAMP" if dialect_name == "postgresql" else "DATETIME"


def apply_missing_columns(engine: Engine) -> None:
    """Añade columnas al modelo `users` que falten en la tabla existente."""
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        # DB fresca: `Base.metadata.create_all` la creará completa.
        return

    existing = {col["name"] for col in inspector.get_columns("users")}
    ts = _timestamp_type(engine.dialect.name)

    migrations: list[tuple[str, str, str | None]] = [
        (
            "reset_password_token",
            "ALTER TABLE users ADD COLUMN reset_password_token VARCHAR(255)",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_reset_password_token "
            "ON users (reset_password_token)",
        ),
        (
            "reset_password_token_expires_at",
            f"ALTER TABLE users ADD COLUMN reset_password_token_expires_at {ts}",
            None,
        ),
    ]

    with engine.begin() as conn:
        for column, add_sql, index_sql in migrations:
            if column in existing:
                continue
            logger.info("Aplicando migración: añadiendo columna users.%s", column)
            conn.execute(text(add_sql))
            if index_sql:
                conn.execute(text(index_sql))
