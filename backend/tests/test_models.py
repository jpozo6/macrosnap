"""Tests para los modelos SQLAlchemy."""

import json

from sqlalchemy.orm import Session

from app.models import Meal


class TestMealModel:
    """Tests para el modelo Meal."""

    def test_crear_meal(self, db_session: Session) -> None:
        meal = Meal(
            meal_name="Test meal",
            calories=100.0,
            protein_g=10.0,
            carbs_g=20.0,
            fat_g=5.0,
            fiber_g=2.0,
        )
        db_session.add(meal)
        db_session.commit()
        db_session.refresh(meal)

        assert meal.id is not None
        assert meal.meal_name == "Test meal"
        assert meal.created_at is not None

    def test_foods_serialization(self, db_session: Session) -> None:
        meal = Meal(
            meal_name="Comida test",
            calories=300.0,
            protein_g=25.0,
            carbs_g=35.0,
            fat_g=12.0,
            fiber_g=4.0,
        )
        foods_data = [
            {"name": "pollo", "confidence": 0.95, "amount": 150, "unit": "g"},
            {"name": "arroz", "confidence": 0.90, "amount": 200, "unit": "g"},
        ]
        meal.foods = foods_data
        db_session.add(meal)
        db_session.commit()
        db_session.refresh(meal)

        assert meal.foods == foods_data
        assert isinstance(meal.foods_json, str)
        assert json.loads(meal.foods_json) == foods_data

    def test_foods_default_vacio(self, db_session: Session) -> None:
        meal = Meal(
            meal_name="Sin foods",
            calories=0, protein_g=0, carbs_g=0, fat_g=0, fiber_g=0,
        )
        db_session.add(meal)
        db_session.commit()
        db_session.refresh(meal)

        assert meal.foods == []

    def test_image_base64_nullable(self, db_session: Session) -> None:
        meal = Meal(
            meal_name="Sin imagen",
            calories=100, protein_g=10, carbs_g=10, fat_g=5, fiber_g=1,
            image_base64=None,
        )
        db_session.add(meal)
        db_session.commit()

        assert meal.image_base64 is None

    def test_meal_con_imagen(self, db_session: Session) -> None:
        fake_b64 = "aW1hZ2VuX2RlX3Rlc3Q="
        meal = Meal(
            meal_name="Con imagen",
            calories=200, protein_g=15, carbs_g=25, fat_g=8, fiber_g=3,
            image_base64=fake_b64,
        )
        db_session.add(meal)
        db_session.commit()
        db_session.refresh(meal)

        assert meal.image_base64 == fake_b64
