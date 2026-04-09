"""Fixtures compartidos para los tests de MacroSnap."""

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models import Meal

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
def client(db_session: Session) -> TestClient:
    """Cliente de test de FastAPI con BD de test inyectada."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_meal(db_session: Session) -> Meal:
    """Crea una comida de ejemplo en la BD de test."""
    meal = Meal(
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
def sample_meals(db_session: Session) -> list[Meal]:
    """Crea varias comidas de ejemplo para tests de listado."""
    meals = []
    for i, (name, cal) in enumerate([
        ("Ensalada César", 280.0),
        ("Pasta boloñesa", 520.0),
        ("Sopa de verduras", 150.0),
    ]):
        meal = Meal(
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
