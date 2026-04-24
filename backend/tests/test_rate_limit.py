"""Tests del rate limit aplicado a los endpoints sensibles de /auth.

El limiter está desactivado por defecto en `conftest.py`. Aquí lo reactivamos
y forzamos límites cortos vía overrides de settings para poder observar el 429
sin generar cientos de peticiones.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rate_limit import limiter


@pytest.fixture
def rate_limited_client(
    anon_client: TestClient,
) -> Generator[TestClient, None, None]:
    """Activa el rate limiter durante el test y limpia su storage al terminar."""
    limiter.enabled = True
    # Contadores globales: resetear antes y después para no contaminar entre tests.
    limiter.reset()
    try:
        yield anon_client
    finally:
        limiter.reset()
        limiter.enabled = False


class TestRateLimitLogin:
    """POST /api/v1/auth/login está protegido contra fuerza bruta."""

    def test_devuelve_429_tras_superar_limite(self, rate_limited_client: TestClient) -> None:
        # Default: 5/minute. A la 6ª petición debe cortar.
        payload = {"email": "nope@example.com", "password": "whatever"}
        for _ in range(5):
            r = rate_limited_client.post("/api/v1/auth/login", json=payload)
            assert r.status_code == 401  # credenciales incorrectas, pero aún dentro del límite

        blocked = rate_limited_client.post("/api/v1/auth/login", json=payload)
        assert blocked.status_code == 429

    def test_limiter_desactivado_no_bloquea(self, anon_client: TestClient) -> None:
        # Con el limiter apagado (default en tests) podemos hacer muchas más peticiones.
        payload = {"email": "nope@example.com", "password": "whatever"}
        for _ in range(20):
            r = anon_client.post("/api/v1/auth/login", json=payload)
            assert r.status_code == 401


class TestRateLimitForgotPassword:
    """POST /api/v1/auth/forgot-password está protegido contra flooding de emails."""

    def test_devuelve_429_tras_superar_limite(self, rate_limited_client: TestClient) -> None:
        # Default: 3/hour.
        payload = {"email": "cualquiera@example.com"}
        for _ in range(3):
            r = rate_limited_client.post("/api/v1/auth/forgot-password", json=payload)
            assert r.status_code == 200

        blocked = rate_limited_client.post("/api/v1/auth/forgot-password", json=payload)
        assert blocked.status_code == 429


class TestRateLimitRegister:
    """POST /api/v1/auth/register también está protegido."""

    def test_devuelve_429_tras_superar_limite(self, rate_limited_client: TestClient) -> None:
        # Default: 5/hour.
        for i in range(5):
            r = rate_limited_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"u{i}@example.com",
                    "email_confirm": f"u{i}@example.com",
                    "password": "Password123!",
                },
            )
            assert r.status_code == 201

        blocked = rate_limited_client.post(
            "/api/v1/auth/register",
            json={
                "email": "otro@example.com",
                "email_confirm": "otro@example.com",
                "password": "Password123!",
            },
        )
        assert blocked.status_code == 429


class TestRateLimitEndpointsIndependientes:
    """El contador es por endpoint, no compartido entre todos los endpoints."""

    def test_limite_de_login_no_bloquea_forgot_password(
        self, rate_limited_client: TestClient,
    ) -> None:
        for _ in range(5):
            rate_limited_client.post(
                "/api/v1/auth/login",
                json={"email": "x@example.com", "password": "wrong"},
            )
        # Consumimos todo el límite de login; forgot-password debe seguir disponible.
        r = rate_limited_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "x@example.com"},
        )
        assert r.status_code == 200
