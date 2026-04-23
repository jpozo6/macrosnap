"""Schemas Pydantic para validación de request/response."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator


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


# ===== Auth =====


class UserCreate(BaseModel):
    """Datos para registro de un nuevo usuario."""

    email: EmailStr
    email_confirm: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def _emails_match(self) -> "UserCreate":
        if self.email.lower() != self.email_confirm.lower():
            raise ValueError("Los correos electrónicos no coinciden.")
        return self


class UserLogin(BaseModel):
    """Credenciales para login."""

    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Información pública de un usuario."""

    id: int
    email: EmailStr
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT devuelto tras login."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageResponse(BaseModel):
    """Respuesta genérica con mensaje."""

    message: str


class ResendVerificationRequest(BaseModel):
    """Petición para reenviar el email de verificación."""

    email: EmailStr
