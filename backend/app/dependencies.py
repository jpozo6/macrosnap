"""Dependencies de FastAPI compartidos (auth)."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resuelve el usuario autenticado a partir del Bearer token."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exc

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exc

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise credentials_exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exc
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email no verificado. Revisa tu bandeja de entrada.",
        )
    return user
