"""Migraciones in-place idempotentes ejecutadas al arrancar la app.

El proyecto todavía no usa Alembic (ver `migrations/README.md`) y se apoya en
`Base.metadata.create_all(bind=engine)` para crear el schema. `create_all` no
añade columnas a tablas ya existentes, así que cuando se mergea una feature
que añade columnas al modelo (p. ej. el flujo de reset de contraseña en
`2288fc6`, o los campos de bolo en `Meal` en el PR 2 del pivot a diabéticos),
las bases de datos en producción se quedan desincronizadas y los endpoints
fallan con 500 `UndefinedColumn`.

Este módulo aplica los `ALTER TABLE ADD COLUMN` necesarios de forma idempotente
en cada arranque. Sustituirlo por Alembic cuando crezca la base de usuarios.
"""

from __future__ import annotations

import logging

from sqlalchemy import Engine, inspect, text

logger = logging.getLogger(__name__)

# Cada entrada: (nombre_columna, DDL_add, DDL_extra_opcional_p_ej_indice)
_ColumnMigration = tuple[str, str, str | None]


def _timestamp_type(dialect_name: str) -> str:
    # Postgres usa TIMESTAMP; SQLite acepta DATETIME (afinidad textual).
    return "TIMESTAMP" if dialect_name == "postgresql" else "DATETIME"


def _users_migrations(dialect: str) -> list[_ColumnMigration]:
    ts = _timestamp_type(dialect)
    return [
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


def _meals_migrations(_dialect: str) -> list[_ColumnMigration]:
    """Columnas del bolo de insulina añadidas en el PR 2 del pivot a diabéticos."""
    return [
        ("glucose_mg_dl", "ALTER TABLE meals ADD COLUMN glucose_mg_dl INTEGER", None),
        ("exercise_level", "ALTER TABLE meals ADD COLUMN exercise_level VARCHAR(20)", None),
        ("slot", "ALTER TABLE meals ADD COLUMN slot VARCHAR(20)", None),
        ("rations_hc", "ALTER TABLE meals ADD COLUMN rations_hc FLOAT", None),
        ("bolus_carb_units", "ALTER TABLE meals ADD COLUMN bolus_carb_units FLOAT", None),
        (
            "bolus_correction_units",
            "ALTER TABLE meals ADD COLUMN bolus_correction_units FLOAT",
            None,
        ),
        (
            "bolus_suggested_units",
            "ALTER TABLE meals ADD COLUMN bolus_suggested_units FLOAT",
            None,
        ),
        ("bolus_total_units", "ALTER TABLE meals ADD COLUMN bolus_total_units FLOAT", None),
    ]


def _apply_table_migrations(
    engine: Engine, table: str, migrations: list[_ColumnMigration]
) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(table):
        # DB fresca: `Base.metadata.create_all` ya creará la tabla completa.
        return
    existing = {col["name"] for col in inspector.get_columns(table)}
    with engine.begin() as conn:
        for column, add_sql, extra_sql in migrations:
            if column in existing:
                continue
            logger.info("Aplicando migración: añadiendo columna %s.%s", table, column)
            conn.execute(text(add_sql))
            if extra_sql:
                conn.execute(text(extra_sql))


def apply_missing_columns(engine: Engine) -> None:
    """Añade columnas que falten en las tablas existentes."""
    dialect = engine.dialect.name
    _apply_table_migrations(engine, "users", _users_migrations(dialect))
    _apply_table_migrations(engine, "meals", _meals_migrations(dialect))
