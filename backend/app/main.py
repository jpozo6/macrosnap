"""FastAPI app entry point para MacroSnap."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.db import Base, engine
from app.rate_limit import limiter
from app.routers import analysis, auth, meals
from app.services.langsmith import setup_langsmith

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar LangSmith tracing
setup_langsmith()

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MacroSnap API",
    description="API para análisis de macronutrientes por imagen usando Gemini Flash",
    version="0.1.0",
)

# Rate limiter: registra el handler de 429 y el middleware que lee el state.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(meals.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Endpoint de health check."""
    return {"status": "ok"}
