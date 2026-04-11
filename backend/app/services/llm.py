"""Inicialización del modelo Gemini Flash via LangChain."""

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


def get_llm() -> ChatGoogleGenerativeAI:
    """Crea una instancia del modelo Gemini Flash."""
    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY no configurada. "
            "Copia backend/.env.example a backend/.env y configura tu API key."
        )
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=settings.google_api_key,
        temperature=0.1,
    )
