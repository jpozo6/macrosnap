"""Schemas Pydantic para validación de request/response."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.services.bolus import ExerciseLevel, TimeSlot


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


class BolusData(BaseModel):
    """Sub-objeto con los datos del bolo de insulina de una comida.

    Está como bloque anidado dentro de `MealResponse` (en vez de campos sueltos
    al mismo nivel que los macros) para que la UI sepa de un vistazo si la
    comida tiene bolo registrado o no (`meal.bolus is None`).
    """

    glucose_mg_dl: int
    exercise_level: str            # 'none' | 'moderate' | 'intense'
    slot: str                      # 'breakfast' | 'lunch' | 'dinner'
    rations_hc: float
    bolus_carb_units: float
    bolus_correction_units: float
    bolus_suggested_units: float   # lo que sugirió la app
    bolus_total_units: float       # lo que el usuario eligió administrar


class MealResponse(BaseModel):
    """Respuesta de una comida del histórico."""

    id: int
    meal_name: str
    macros: MacroNutrients
    foods: list[FoodItem]
    image_base64: str | None = None
    created_at: datetime
    bolus: BolusData | None = None

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


class ForgotPasswordRequest(BaseModel):
    """Petición para iniciar el flujo de reset de contraseña."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Petición para establecer una nueva contraseña a partir del token."""

    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)
    new_password_confirm: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def _passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.new_password_confirm:
            raise ValueError("Las contraseñas no coinciden.")
        return self


# ===== Perfil diabético y bolo de insulina =====

_VALID_ROUNDING_STEPS = (0.1, 0.5, 1.0)


class DiabeticProfileUpsert(BaseModel):
    """Datos para crear o actualizar el perfil diabético del usuario."""

    ration_grams: int = Field(default=10, ge=1, le=20)
    target_glucose: int = Field(default=110, ge=70, le=180)
    hypo_threshold: int = Field(default=70, ge=50, le=100)
    bolus_rounding_step: float = Field(default=0.5)

    # Ajuste por ejercicio. Fracción negativa (-0.20 = baja un 20%).
    exercise_moderate_factor: float = Field(default=-0.20, ge=-0.9, le=0.0)
    exercise_intense_factor: float = Field(default=-0.40, ge=-0.9, le=0.0)

    # Ratios por franja: IPR (U/ración), ISF (mg/dL bajada por U).
    ipr_breakfast: float = Field(ge=0.1, le=10)
    ipr_lunch: float = Field(ge=0.1, le=10)
    ipr_dinner: float = Field(ge=0.1, le=10)
    isf_breakfast: int = Field(ge=5, le=400)
    isf_lunch: int = Field(ge=5, le=400)
    isf_dinner: int = Field(ge=5, le=400)

    @field_validator("bolus_rounding_step")
    @classmethod
    def _valid_rounding_step(cls, v: float) -> float:
        if v not in _VALID_ROUNDING_STEPS:
            raise ValueError(
                f"bolus_rounding_step debe ser uno de {_VALID_ROUNDING_STEPS}"
            )
        return v


class DiabeticProfileOut(BaseModel):
    """Perfil diabético serializado para respuesta."""

    id: int
    ration_grams: int
    target_glucose: int
    hypo_threshold: int
    bolus_rounding_step: float
    exercise_moderate_factor: float
    exercise_intense_factor: float
    ipr_breakfast: float
    ipr_lunch: float
    ipr_dinner: float
    isf_breakfast: int
    isf_lunch: int
    isf_dinner: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BolusCalcRequest(BaseModel):
    """Datos puntuales de la comida para calcular el bolo sugerido."""

    carbs_g: float = Field(ge=0, le=1000)
    glucose: int = Field(ge=20, le=600, description="Glucemia actual en mg/dL")
    exercise: ExerciseLevel = ExerciseLevel.NONE
    slot: TimeSlot


class BolusCalcResponse(BaseModel):
    """Desglose del bolo sugerido. La UI muestra cada componente al usuario."""

    rations: float
    bolus_carb: float
    bolus_correction: float
    exercise_factor: float
    bolus_before_round: float
    bolus_total: float
    hypoglycemia_warning: bool


class MealBolusPatch(BaseModel):
    """Datos que el mobile envía al confirmar el bolo de una comida.

    El servidor recalcula el desglose para garantizar coherencia con el
    perfil actual del usuario (no nos fiamos de lo que mande el cliente,
    salvo de `bolus_chosen_units`, que es la cifra final que el usuario
    decidió administrarse — puede diferir del sugerido).
    """

    glucose: int = Field(ge=20, le=600, description="Glucemia actual en mg/dL")
    exercise: ExerciseLevel
    slot: TimeSlot
    bolus_chosen_units: float = Field(ge=0, le=50)
