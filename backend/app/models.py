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
    diabetic_profile = relationship(
        "DiabeticProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class DiabeticProfile(Base):
    """Perfil clínico del usuario diabético.

    1:1 con `User`. Si no existe, el modo diabético está desactivado.

    Las franjas horarias son fijas (modelo "Opción A"): desayuno 00-11h,
    comida 11-17h, cena 17-24h. Si en el futuro se quieren franjas
    configurables, esto se moverá a una tabla aparte `diabetic_profile_slots`.
    """

    __tablename__ = "diabetic_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # Configuración general
    ration_grams = Column(Integer, nullable=False, default=10)
    target_glucose = Column(Integer, nullable=False, default=110)  # mg/dL
    hypo_threshold = Column(Integer, nullable=False, default=70)  # mg/dL
    bolus_rounding_step = Column(Float, nullable=False, default=0.5)

    # Ajuste por ejercicio (fracción: -0.20 = -20%)
    exercise_moderate_factor = Column(Float, nullable=False, default=-0.20)
    exercise_intense_factor = Column(Float, nullable=False, default=-0.40)

    # Ratios por franja horaria. IPR = insulina/ración (U). ISF = mg/dL bajada por U.
    ipr_breakfast = Column(Float, nullable=False)
    ipr_lunch = Column(Float, nullable=False)
    ipr_dinner = Column(Float, nullable=False)
    isf_breakfast = Column(Integer, nullable=False)
    isf_lunch = Column(Integer, nullable=False)
    isf_dinner = Column(Integer, nullable=False)

    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="diabetic_profile")


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

    # Datos del bolo de insulina (sólo se rellenan si el usuario tiene
    # `DiabeticProfile` y ha pasado por la pantalla de bolo tras el análisis).
    # Todas nullable: las comidas sin bolo (modo no diabético o antiguas) las
    # tienen a NULL.
    glucose_mg_dl = Column(Integer, nullable=True)
    exercise_level = Column(String(20), nullable=True)         # 'none' | 'moderate' | 'intense'
    slot = Column(String(20), nullable=True)                   # 'breakfast' | 'lunch' | 'dinner'
    rations_hc = Column(Float, nullable=True)
    bolus_carb_units = Column(Float, nullable=True)
    bolus_correction_units = Column(Float, nullable=True)
    bolus_suggested_units = Column(Float, nullable=True)       # lo que sugirió la app
    bolus_total_units = Column(Float, nullable=True)           # lo que el usuario eligió

    user = relationship("User", back_populates="meals")

    @property
    def foods(self) -> list[dict]:
        """Deserializa los alimentos desde JSON."""
        return json.loads(self.foods_json) if self.foods_json else []

    @foods.setter
    def foods(self, value: list[dict]) -> None:
        """Serializa los alimentos a JSON."""
        self.foods_json = json.dumps(value, ensure_ascii=False)
