"""Configuración de la aplicación usando pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración principal de MacroSnap."""

    google_api_key: str = ""
    langsmith_api_key: str = ""
    langsmith_project: str = "macrosnap"
    database_url: str = "sqlite:///./macrosnap.db"

    # JWT
    secret_key: str = "change-me-in-production-please-use-a-long-random-string"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 días
    jwt_algorithm: str = "HS256"

    # Verificación de email
    verification_token_expire_hours: int = 24

    # SMTP (rellenar en .env)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_from_name: str = "MacroSnap"
    smtp_use_tls: bool = True
    smtp_start_tls: bool = True

    # URL pública del frontend para construir el link de verificación.
    # Para Expo dev: http://localhost:8081 ; producción web: tu dominio.
    frontend_url: str = "http://localhost:8081"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
