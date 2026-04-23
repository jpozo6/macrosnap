"""Tests para los endpoints de autenticación."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User


class TestRegister:
    """POST /api/v1/auth/register."""

    def test_registro_correcto(self, anon_client: TestClient, db_session: Session) -> None:
        response = anon_client.post(
            "/api/v1/auth/register",
            json={
                "email": "nuevo@example.com",
                "email_confirm": "nuevo@example.com",
                "password": "Password123!",
            },
        )
        assert response.status_code == 201
        u = db_session.query(User).filter(User.email == "nuevo@example.com").first()
        assert u is not None
        assert u.is_verified is False
        assert u.verification_token is not None
        assert u.hashed_password != "Password123!"  # debe estar hasheado

    def test_registro_email_normalizado(self, anon_client: TestClient, db_session: Session) -> None:
        response = anon_client.post(
            "/api/v1/auth/register",
            json={
                "email": "  MixedCase@Example.COM  ",
                "email_confirm": "mixedcase@example.com",
                "password": "Password123!",
            },
        )
        assert response.status_code == 201
        u = db_session.query(User).filter(User.email == "mixedcase@example.com").first()
        assert u is not None

    def test_emails_no_coinciden(self, anon_client: TestClient) -> None:
        response = anon_client.post(
            "/api/v1/auth/register",
            json={
                "email": "a@example.com",
                "email_confirm": "b@example.com",
                "password": "Password123!",
            },
        )
        assert response.status_code == 422

    def test_email_duplicado(self, anon_client: TestClient, user: User) -> None:
        response = anon_client.post(
            "/api/v1/auth/register",
            json={
                "email": user.email,
                "email_confirm": user.email,
                "password": "Password123!",
            },
        )
        assert response.status_code == 409

    def test_password_demasiado_corto(self, anon_client: TestClient) -> None:
        response = anon_client.post(
            "/api/v1/auth/register",
            json={
                "email": "x@example.com",
                "email_confirm": "x@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422

    def test_email_invalido(self, anon_client: TestClient) -> None:
        response = anon_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "email_confirm": "not-an-email",
                "password": "Password123!",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login."""

    def test_login_ok(self, anon_client: TestClient, user: User) -> None:
        response = anon_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "Password123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert data["access_token"]
        assert data["user"]["email"] == user.email

    def test_login_password_incorrecta(self, anon_client: TestClient, user: User) -> None:
        response = anon_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "wrong-password"},
        )
        assert response.status_code == 401

    def test_login_usuario_no_existe(self, anon_client: TestClient) -> None:
        response = anon_client.post(
            "/api/v1/auth/login",
            json={"email": "nope@example.com", "password": "Password123!"},
        )
        assert response.status_code == 401

    def test_login_no_verificado(self, anon_client: TestClient, unverified_user: User) -> None:
        response = anon_client.post(
            "/api/v1/auth/login",
            json={"email": unverified_user.email, "password": "Password123!"},
        )
        assert response.status_code == 403


class TestVerifyEmail:
    """GET /api/v1/auth/verify-email."""

    def test_verifica_token_valido(
        self, anon_client: TestClient, db_session: Session, unverified_user: User,
    ) -> None:
        unverified_user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db_session.commit()

        response = anon_client.get(
            f"/api/v1/auth/verify-email?token={unverified_user.verification_token}"
        )
        assert response.status_code == 200

        db_session.refresh(unverified_user)
        assert unverified_user.is_verified is True
        assert unverified_user.verification_token is None

    def test_token_caducado(
        self, anon_client: TestClient, db_session: Session, unverified_user: User,
    ) -> None:
        unverified_user.verification_token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.commit()

        response = anon_client.get(
            f"/api/v1/auth/verify-email?token={unverified_user.verification_token}"
        )
        assert response.status_code == 400

    def test_token_invalido(self, anon_client: TestClient) -> None:
        response = anon_client.get("/api/v1/auth/verify-email?token=does-not-exist")
        assert response.status_code == 400


class TestMe:
    """GET /api/v1/auth/me."""

    def test_me_requiere_auth(self, anon_client: TestClient) -> None:
        response = anon_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_devuelve_usuario(self, client: TestClient, user: User) -> None:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["is_verified"] is True


class TestResendVerification:
    """POST /api/v1/auth/resend-verification."""

    def test_reenvia_a_usuario_no_verificado(
        self, anon_client: TestClient, db_session: Session, unverified_user: User,
    ) -> None:
        old_token = unverified_user.verification_token
        response = anon_client.post(
            "/api/v1/auth/resend-verification",
            json={"email": unverified_user.email},
        )
        assert response.status_code == 200
        db_session.refresh(unverified_user)
        # El token se ha rotado
        assert unverified_user.verification_token != old_token

    def test_respuesta_genérica_para_email_no_existente(self, anon_client: TestClient) -> None:
        response = anon_client.post(
            "/api/v1/auth/resend-verification",
            json={"email": "fantasma@example.com"},
        )
        # Devolvemos 200 para no filtrar existencia de cuentas.
        assert response.status_code == 200
