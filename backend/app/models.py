"""Modelos SQLAlchemy para la base de datos."""

import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    """Usuario registrado de MacroSnap."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_token = Column(String(255), nullable=True, unique=True, index=True)
    verification_token_expires_at = Column(DateTime, nullable=True)
    reset_password_token = Column(String(255), nullable=True, unique=True, index=True)
    reset_password_token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")


class Meal(Base):
    """Modelo de una comida analizada."""

    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
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

    user = relationship("User", back_populates="meals")

    @property
    def foods(self) -> list[dict]:
        """Deserializa los alimentos desde JSON."""
        return json.loads(self.foods_json) if self.foods_json else []

    @foods.setter
    def foods(self, value: list[dict]) -> None:
        """Serializa los alimentos a JSON."""
        self.foods_json = json.dumps(value, ensure_ascii=False)
