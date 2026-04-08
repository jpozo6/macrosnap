"""Configuración de LangSmith para observabilidad y tracing."""

import os

from app.config import settings


def setup_langsmith() -> None:
    """Configura las variables de entorno para LangSmith tracing."""
    if settings.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
