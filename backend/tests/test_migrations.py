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
