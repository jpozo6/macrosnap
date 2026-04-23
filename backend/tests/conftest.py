"""Fixtures compartidos para los tests de MacroSnap."""

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, get_db
from app.dependencies import get_current_user
from app.main import app
from app.models import Meal, User
from app.security import create_access_token, hash_password

# SQLite in-memory con StaticPool para compartir la misma conexión entre threads
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db() -> Generator[None, None, None]:
    """Crea y destruye las tablas para cada test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provee una sesión de base de datos de test."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def user(db_session: Session) -> User:
    """Usuario de prueba ya verificado."""
    u = User(
        email="test@example.com",
        hashed_password=hash_password("Password123!"),
        is_verified=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def other_user(db_session: Session) -> User:
    """Segundo usuario, útil para tests de aislamiento."""
    u = User(
        email="otro@example.com",
        hashed_password=hash_password("Password123!"),
        is_verified=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def unverified_user(db_session: Session) -> User:
    """Usuario registrado pero sin verificar email."""
    u = User(
        email="pending@example.com",
        hashed_password=hash_password("Password123!"),
        is_verified=False,
        verification_token="test-verification-token-abc123",
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def _build_client(db_session: Session, current_user: User | None) -> TestClient:
    """Crea un TestClient con BD inyectada y, opcionalmente, usuario autenticado."""
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app)


@pytest.fixture
def anon_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente sin autenticación (para probar endpoints públicos o 401)."""
    with _build_client(db_session, None) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client(db_session: Session, user: User) -> Generator[TestClient, None, None]:
    """Cliente autenticado como `user` (default para la mayoría de tests)."""
    with _build_client(db_session, user) as c:
        # Header Authorization real para los tests que pasan por OAuth2 scheme
        token = create_access_token(subject=user.id)
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_meal(db_session: Session, user: User) -> Meal:
    """Crea una comida de ejemplo en la BD de test, asociada al usuario."""
    meal = Meal(
        user_id=user.id,
        meal_name="Arroz con pollo",
        calories=450.0,
        protein_g=30.5,
        carbs_g=45.2,
        fat_g=15.8,
        fiber_g=5.3,
        image_base64=None,
    )
    meal.foods = [
        {"name": "arroz blanco", "confidence": 0.95, "amount": 200, "unit": "g"},
        {"name": "pechuga de pollo", "confidence": 0.92, "amount": 150, "unit": "g"},
    ]
    db_session.add(meal)
    db_session.commit()
    db_session.refresh(meal)
    return meal


@pytest.fixture
def sample_meals(db_session: Session, user: User) -> list[Meal]:
    """Crea varias comidas de ejemplo para tests de listado."""
    meals = []
    for i, (name, cal) in enumerate([
        ("Ensalada César", 280.0),
        ("Pasta boloñesa", 520.0),
        ("Sopa de verduras", 150.0),
    ]):
        meal = Meal(
            user_id=user.id,
            meal_name=name,
            calories=cal,
            protein_g=20.0 + i * 5,
            carbs_g=30.0 + i * 10,
            fat_g=10.0 + i * 3,
            fiber_g=3.0 + i,
            created_at=datetime(2026, 4, 9, 12 + i, 0, 0, tzinfo=timezone.utc),
        )
        meal.foods = [{"name": name.lower(), "confidence": 0.9, "amount": 300, "unit": "g"}]
        db_session.add(meal)
        meals.append(meal)
    db_session.commit()
    for m in meals:
        db_session.refresh(m)
    return meals
