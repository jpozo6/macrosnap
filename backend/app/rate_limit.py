"""Rate limiter compartido para endpoints sensibles (slowapi).

Se expone un único `limiter` que los routers decoran con `@limiter.limit(...)`.
Se apoya en la IP del cliente y puede desactivarse por configuración (útil en
tests para no depender de temporizaciones o contadores globales).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
    default_limits=[],
)
