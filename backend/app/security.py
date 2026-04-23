"""Utilidades de seguridad: hashing de passwords y JWT."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# bcrypt truncaría silenciosamente cualquier password > 72 bytes; lo truncamos
# nosotros de forma explícita para mantener consistencia entre hash y verify.
_BCRYPT_MAX_BYTES = 72


def _encode(plain_password: str) -> bytes:
    data = plain_password.encode("utf-8")
    return data[:_BCRYPT_MAX_BYTES]


def hash_password(plain_password: str) -> str:
    """Devuelve el hash bcrypt de una contraseña en texto plano."""
    return bcrypt.hashpw(_encode(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash."""
    try:
        return bcrypt.checkpw(_encode(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    """Genera un JWT firmado con el `sub` indicado."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decodifica y valida un JWT. Devuelve el payload o None si es inválido."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def generate_verification_token() -> str:
    """Genera un token URL-safe para verificación de email."""
    return secrets.token_urlsafe(48)
