"""Cálculo del bolo de insulina prandial + corrección.

Función pura sin dependencias de FastAPI / DB: recibe un perfil clínico
y los datos puntuales de la comida, devuelve el desglose del bolo.

Convenciones (España, validadas con el usuario):
- 1 ración = 10 g de hidratos de carbono (configurable en el perfil).
- Glucemias en mg/dL únicamente.
- 3 franjas horarias fijas: desayuno (00-11), comida (11-17), cena (17-24).
- El bolo final NUNCA es negativo: se hace `max(0, ...)` antes de redondear.
- La hipoglucemia (`glucose < hypo_threshold`) NO bloquea: se calcula igual
  pero se emite un flag `hypoglycemia_warning` para que la UI sugiera al
  usuario consumir HC rápidos antes de inyectarse.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from app.models import DiabeticProfile


class TimeSlot(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


class ExerciseLevel(str, Enum):
    NONE = "none"
    MODERATE = "moderate"
    INTENSE = "intense"


@dataclass(frozen=True)
class BolusBreakdown:
    """Desglose detallado del cálculo del bolo, pensado para mostrarse en UI."""

    rations: float                  # carbs_g / ration_grams, 1 decimal
    bolus_carb: float               # rations × IPR del slot
    bolus_correction: float         # (glucose - target) / ISF — puede ser <0
    exercise_factor: float          # 0, mod o intense (fracción, p. ej. -0.20)
    bolus_before_round: float       # max(0, (carb + corr) × (1 + ex))
    bolus_total: float              # bolus_before_round redondeado al step
    hypoglycemia_warning: bool      # glucose < hypo_threshold


def _ipr_for_slot(profile: DiabeticProfile, slot: TimeSlot) -> float:
    return {
        TimeSlot.BREAKFAST: profile.ipr_breakfast,
        TimeSlot.LUNCH: profile.ipr_lunch,
        TimeSlot.DINNER: profile.ipr_dinner,
    }[slot]


def _isf_for_slot(profile: DiabeticProfile, slot: TimeSlot) -> int:
    return {
        TimeSlot.BREAKFAST: profile.isf_breakfast,
        TimeSlot.LUNCH: profile.isf_lunch,
        TimeSlot.DINNER: profile.isf_dinner,
    }[slot]


def _exercise_factor(profile: DiabeticProfile, exercise: ExerciseLevel) -> float:
    if exercise == ExerciseLevel.MODERATE:
        return float(profile.exercise_moderate_factor)
    if exercise == ExerciseLevel.INTENSE:
        return float(profile.exercise_intense_factor)
    return 0.0


def _round_to_step(value: float, step: float) -> float:
    """Redondea `value` al múltiplo más cercano de `step`, half-up.

    Usa Decimal para evitar el "banker's rounding" de Python en .5 — para
    dosis médicas es más intuitivo que 2.75 redondee a 3.0 con step=0.5,
    no a 2.5 como haría `round()`.
    """
    if step <= 0:
        return value
    quantized = (Decimal(str(value)) / Decimal(str(step))).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return float(quantized * Decimal(str(step)))


def calculate_bolus(
    carbs_g: float,
    glucose_mg_dl: int,
    exercise: ExerciseLevel,
    slot: TimeSlot,
    profile: DiabeticProfile,
) -> BolusBreakdown:
    """Calcula el bolo prandial + corrección para la comida.

    :param carbs_g: HC totales de la comida en gramos.
    :param glucose_mg_dl: glucemia capilar actual.
    :param exercise: intensidad del ejercicio reciente o previsto.
    :param slot: franja horaria de la comida.
    :param profile: perfil clínico del usuario.
    """
    ipr = _ipr_for_slot(profile, slot)
    isf = _isf_for_slot(profile, slot)

    rations = round(carbs_g / profile.ration_grams, 1)
    bolus_carb = rations * ipr
    bolus_correction = (glucose_mg_dl - profile.target_glucose) / isf
    exercise_factor = _exercise_factor(profile, exercise)

    bolus_before_round = max(0.0, (bolus_carb + bolus_correction) * (1 + exercise_factor))
    bolus_total = _round_to_step(bolus_before_round, profile.bolus_rounding_step)

    return BolusBreakdown(
        rations=rations,
        bolus_carb=round(bolus_carb, 2),
        bolus_correction=round(bolus_correction, 2),
        exercise_factor=exercise_factor,
        bolus_before_round=round(bolus_before_round, 2),
        bolus_total=bolus_total,
        hypoglycemia_warning=glucose_mg_dl < profile.hypo_threshold,
    )
