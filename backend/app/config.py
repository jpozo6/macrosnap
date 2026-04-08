"""Configuración de la aplicación usando pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración principal de MacroSnap."""

    google_api_key: str = ""
    langsmith_api_key: str = ""
    langsmith_project: str = "macrosnap"
    database_url: str = "sqlite:///./macrosnap.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
