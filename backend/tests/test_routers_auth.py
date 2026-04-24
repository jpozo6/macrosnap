"""Tests para los endpoints de autenticación."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from app.security import verify_password


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


class TestForgotPassword:
    """POST /api/v1/auth/forgot-password."""

    def test_genera_token_para_usuario_existente(
        self, anon_client: TestClient, db_session: Session, user: User,
    ) -> None:
        assert user.reset_password_token is None
        response = anon_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": user.email},
        )
        assert response.status_code == 200
        db_session.refresh(user)
        assert user.reset_password_token is not None
        assert user.reset_password_token_expires_at is not None

    def test_respuesta_genérica_para_email_no_existente(self, anon_client: TestClient) -> None:
        response = anon_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "fantasma@example.com"},
        )
        # Devolvemos 200 para no filtrar existencia de cuentas.
        assert response.status_code == 200

    def test_email_normalizado(
        self, anon_client: TestClient, db_session: Session, user: User,
    ) -> None:
        response = anon_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": f"  {user.email.upper()}  "},
        )
        assert response.status_code == 200
        db_session.refresh(user)
        assert user.reset_password_token is not None

    def test_token_se_rota_en_peticiones_sucesivas(
        self, anon_client: TestClient, db_session: Session, user: User,
    ) -> None:
        anon_client.post("/api/v1/auth/forgot-password", json={"email": user.email})
        db_session.refresh(user)
        first_token = user.reset_password_token
        anon_client.post("/api/v1/auth/forgot-password", json={"email": user.email})
        db_session.refresh(user)
        assert user.reset_password_token != first_token


class TestResetPassword:
    """POST /api/v1/auth/reset-password."""

    def test_resetea_password_con_token_valido(
        self, anon_client: TestClient, db_session: Session, user: User,
    ) -> None:
        user.reset_password_token = "reset-token-abc123"
        user.reset_password_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db_session.commit()

        response = anon_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "reset-token-abc123",
                "new_password": "NewPassword456!",
                "new_password_confirm": "NewPassword456!",
            },
        )
        assert response.status_code == 200

        db_session.refresh(user)
        assert user.reset_password_token is None
        assert user.reset_password_token_expires_at is None
        assert verify_password("NewPassword456!", user.hashed_password)
        assert not verify_password("Password123!", user.hashed_password)

    def test_token_caducado(
        self, anon_client: TestClient, db_session: Session, user: User,
    ) -> None:
        user.reset_password_token = "reset-token-caducado"
        user.reset_password_token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.commit()

        response = anon_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "reset-token-caducado",
                "new_password": "NewPassword456!",
                "new_password_confirm": "NewPassword456!",
            },
        )
        assert response.status_code == 400

        db_session.refresh(user)
        assert verify_password("Password123!", user.hashed_password)

    def test_token_invalido(self, anon_client: TestClient) -> None:
        response = anon_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "token-que-no-existe",
                "new_password": "NewPassword456!",
                "new_password_confirm": "NewPassword456!",
            },
        )
        assert response.status_code == 400

    def test_passwords_no_coinciden(
        self, anon_client: TestClient, db_session: Session, user: User,
    ) -> None:
        user.reset_password_token = "reset-token-xyz"
        user.reset_password_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db_session.commit()

        response = anon_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "reset-token-xyz",
                "new_password": "NewPassword456!",
                "new_password_confirm": "Otra456!",
            },
        )
        assert response.status_code == 422

    def test_password_demasiado_corta(
        self, anon_client: TestClient, db_session: Session, user: User,
    ) -> None:
        user.reset_password_token = "reset-token-corto"
        user.reset_password_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db_session.commit()

        response = anon_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "reset-token-corto",
                "new_password": "short",
                "new_password_confirm": "short",
            },
        )
        assert response.status_code == 422

    def test_token_se_invalida_tras_uso(
        self, anon_client: TestClient, db_session: Session, user: User,
    ) -> None:
        user.reset_password_token = "reset-token-unico"
        user.reset_password_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db_session.commit()

        payload = {
            "token": "reset-token-unico",
            "new_password": "NewPassword456!",
            "new_password_confirm": "NewPassword456!",
        }
        first = anon_client.post("/api/v1/auth/reset-password", json=payload)
        assert first.status_code == 200

        second = anon_client.post("/api/v1/auth/reset-password", json=payload)
        assert second.status_code == 400

    def test_login_con_nueva_password_tras_reset(
        self, anon_client: TestClient, db_session: Session, user: User,
    ) -> None:
        user.reset_password_token = "reset-token-login"
        user.reset_password_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db_session.commit()

        anon_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "reset-token-login",
                "new_password": "NewPassword456!",
                "new_password_confirm": "NewPassword456!",
            },
        )

        response = anon_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "NewPassword456!"},
        )
        assert response.status_code == 200
