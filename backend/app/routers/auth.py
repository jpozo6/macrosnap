"""Router de autenticación: registro, login, verificación de email."""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models import User
from app.rate_limit import limiter
from app.schemas import (
    ForgotPasswordRequest,
    MessageResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.security import (
    create_access_token,
    generate_reset_password_token,
    generate_verification_token,
    hash_password,
    verify_password,
)
from app.services.email import send_reset_password_email, send_verification_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _new_verification(user: User) -> None:
    """Asigna un nuevo token de verificación con expiración a un usuario."""
    user.verification_token = generate_verification_token()
    user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.verification_token_expire_hours
    )


def _new_reset_password(user: User) -> None:
    """Asigna un nuevo token de reset de contraseña con expiración."""
    user.reset_password_token = generate_reset_password_token()
    user.reset_password_token_expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.reset_password_token_expire_hours
    )


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_register)
async def register(
    request: Request,
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Registra un nuevo usuario y envía email de verificación."""
    email = _normalize_email(payload.email)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese email.",
        )

    user = User(email=email, hashed_password=hash_password(payload.password), is_verified=False)
    _new_verification(user)
    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        await send_verification_email(to=email, token=user.verification_token)
    except Exception as e:
        logger.exception("Fallo al enviar email de verificación a %s: %s", email, e)
        # No revertimos el alta: el usuario podrá pedir reenvío en /resend-verification.

    return MessageResponse(
        message="Registro completado. Revisa tu correo para verificar la cuenta."
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_login)
def login(
    request: Request,
    payload: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Autentica con email/password y devuelve un JWT."""
    email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas.",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email no verificado. Revisa tu bandeja de entrada.",
        )
    token = create_access_token(subject=user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/verify-email", response_model=MessageResponse)
def verify_email(
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Verifica el email de un usuario a partir de su token."""
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido.")

    expires = user.verification_token_expires_at
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if not expires or expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token caducado.")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    db.commit()
    return MessageResponse(message="Email verificado correctamente. Ya puedes iniciar sesión.")


@router.post("/resend-verification", response_model=MessageResponse)
@limiter.limit(settings.rate_limit_resend_verification)
async def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Reenvía el email de verificación. Respuesta genérica para no filtrar existencia."""
    email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if user and not user.is_verified:
        _new_verification(user)
        db.commit()
        try:
            await send_verification_email(to=email, token=user.verification_token)
        except Exception as e:
            logger.exception("Fallo al reenviar verificación a %s: %s", email, e)
    return MessageResponse(
        message="Si el email existe y no está verificado, te hemos enviado un nuevo enlace."
    )


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(settings.rate_limit_forgot_password)
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Inicia el flujo de reset. Respuesta genérica para no filtrar existencia."""
    email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if user:
        _new_reset_password(user)
        db.commit()
        try:
            await send_reset_password_email(to=email, token=user.reset_password_token)
        except Exception as e:
            logger.exception("Fallo al enviar email de reset a %s: %s", email, e)
    return MessageResponse(
        message=(
            "Si el email existe, te hemos enviado un enlace para restablecer "
            "la contraseña."
        )
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit(settings.rate_limit_reset_password)
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Establece una nueva contraseña a partir del token de reset."""
    user = db.query(User).filter(User.reset_password_token == payload.token).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido.")

    expires = user.reset_password_token_expires_at
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if not expires or expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token caducado.")

    user.hashed_password = hash_password(payload.new_password)
    user.reset_password_token = None
    user.reset_password_token_expires_at = None
    db.commit()
    return MessageResponse(
        message="Contraseña actualizada correctamente. Ya puedes iniciar sesión."
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Devuelve el usuario autenticado."""
    return UserOut.model_validate(current_user)
