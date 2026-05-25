"""Tests para `app.migrations.apply_missing_columns`."""

from sqlalchemy import StaticPool, create_engine, inspect, text

from app.migrations import apply_missing_columns


def _make_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _create_legacy_users_table(engine) -> None:
    """Recrea la tabla `users` tal y como existía ANTES del feature de reset."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    hashed_password VARCHAR(255) NOT NULL,
                    is_verified BOOLEAN NOT NULL DEFAULT 0,
                    verification_token VARCHAR(255),
                    verification_token_expires_at DATETIME,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )


def test_apply_missing_columns_adds_reset_columns_to_legacy_table() -> None:
    """Una tabla `users` sin las columnas de reset debe quedar al día."""
    engine = _make_engine()
    _create_legacy_users_table(engine)

    apply_missing_columns(engine)

    cols = {c["name"] for c in inspect(engine).get_columns("users")}
    assert "reset_password_token" in cols
    assert "reset_password_token_expires_at" in cols


def test_apply_missing_columns_is_idempotent() -> None:
    """Llamarlo dos veces sobre una tabla ya migrada no debe fallar."""
    engine = _make_engine()
    _create_legacy_users_table(engine)

    apply_missing_columns(engine)
    # La segunda llamada debe ser no-op (no DuplicateColumn).
    apply_missing_columns(engine)

    cols = {c["name"] for c in inspect(engine).get_columns("users")}
    assert "reset_password_token" in cols


def test_apply_missing_columns_noop_when_users_table_missing() -> None:
    """Si la tabla no existe, no debe intentar alterar nada ni romper."""
    engine = _make_engine()
    # No creamos la tabla — `create_all` se encargaría en el flujo real.
    apply_missing_columns(engine)
    assert not inspect(engine).has_table("users")


# ===== Migración de columnas de bolo en `meals` (PR 2 del pivot a diabéticos) =====

_LEGACY_MEALS_DDL = """
CREATE TABLE meals (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    meal_name VARCHAR(255) NOT NULL,
    calories FLOAT NOT NULL DEFAULT 0,
    protein_g FLOAT NOT NULL DEFAULT 0,
    carbs_g FLOAT NOT NULL DEFAULT 0,
    fat_g FLOAT NOT NULL DEFAULT 0,
    fiber_g FLOAT NOT NULL DEFAULT 0,
    foods_json TEXT NOT NULL DEFAULT '[]',
    image_base64 TEXT,
    created_at DATETIME NOT NULL
)
"""

_EXPECTED_MEALS_BOLUS_COLUMNS = {
    "glucose_mg_dl",
    "exercise_level",
    "slot",
    "rations_hc",
    "bolus_carb_units",
    "bolus_correction_units",
    "bolus_suggested_units",
    "bolus_total_units",
}


def _create_legacy_meals_table(engine) -> None:
    """Recrea la tabla `meals` tal y como existía ANTES del PR 2."""
    with engine.begin() as conn:
        conn.execute(text(_LEGACY_MEALS_DDL))


def test_apply_missing_columns_adds_bolus_columns_to_legacy_meals() -> None:
    """Una tabla `meals` antigua debe ganar las 8 columnas del bolo."""
    engine = _make_engine()
    _create_legacy_meals_table(engine)

    apply_missing_columns(engine)

    cols = {c["name"] for c in inspect(engine).get_columns("meals")}
    assert _EXPECTED_MEALS_BOLUS_COLUMNS.issubset(cols)


def test_apply_missing_columns_meals_idempotent() -> None:
    """Dos llamadas seguidas sobre meals no deben romper."""
    engine = _make_engine()
    _create_legacy_meals_table(engine)

    apply_missing_columns(engine)
    apply_missing_columns(engine)

    cols = {c["name"] for c in inspect(engine).get_columns("meals")}
    assert _EXPECTED_MEALS_BOLUS_COLUMNS.issubset(cols)


def test_legacy_meals_row_remains_intact_after_migration() -> None:
    """Filas previas deben sobrevivir con los campos de bolo a NULL."""
    engine = _make_engine()
    _create_legacy_meals_table(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO meals (id, user_id, meal_name, calories, protein_g, "
                "carbs_g, fat_g, fiber_g, foods_json, created_at) "
                "VALUES (1, 1, 'Tortilla', 300, 20, 10, 18, 1, '[]', "
                "'2026-01-01T12:00:00')"
            )
        )

    apply_missing_columns(engine)

    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT meal_name, bolus_total_units, glucose_mg_dl FROM meals "
                "WHERE id=1"
            )
        ).one()
    assert row.meal_name == "Tortilla"
    assert row.bolus_total_units is None
    assert row.glucose_mg_dl is None
