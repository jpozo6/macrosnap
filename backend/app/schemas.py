"""Schemas Pydantic para validación de request/response."""

from datetime import datetime

from pydantic import BaseModel


class FoodItem(BaseModel):
    """Alimento identificado en la imagen."""

    name: str
    confidence: float
    amount: float | None = None
    unit: str | None = None


class MacroNutrients(BaseModel):
    """Macronutrientes calculados."""

    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float


class AnalysisResponse(BaseModel):
    """Respuesta del endpoint de análisis."""

    meal_id: int
    meal_name: str
    macros: MacroNutrients
    foods: list[FoodItem]


class MealResponse(BaseModel):
    """Respuesta de una comida del histórico."""

    id: int
    meal_name: str
    macros: MacroNutrients
    foods: list[FoodItem]
    image_base64: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DailySummaryResponse(BaseModel):
    """Resumen diario de macronutrientes."""

    date: str
    total_meals: int
    macros: MacroNutrients


class ErrorResponse(BaseModel):
    """Respuesta de error."""

    detail: str
