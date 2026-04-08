"""Modelos SQLAlchemy para la base de datos."""

import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.db import Base


class Meal(Base):
    """Modelo de una comida analizada."""

    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    meal_name = Column(String(255), nullable=False)
    calories = Column(Float, nullable=False, default=0)
    protein_g = Column(Float, nullable=False, default=0)
    carbs_g = Column(Float, nullable=False, default=0)
    fat_g = Column(Float, nullable=False, default=0)
    fiber_g = Column(Float, nullable=False, default=0)
    foods_json = Column(Text, nullable=False, default="[]")
    image_base64 = Column(Text, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    @property
    def foods(self) -> list[dict]:
        """Deserializa los alimentos desde JSON."""
        return json.loads(self.foods_json) if self.foods_json else []

    @foods.setter
    def foods(self, value: list[dict]) -> None:
        """Serializa los alimentos a JSON."""
        self.foods_json = json.dumps(value, ensure_ascii=False)
