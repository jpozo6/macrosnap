"""Tests de la función pura `calculate_bolus`.

Verificamos cada componente del desglose por separado para detectar el
origen exacto de cualquier regresión: raciones, bolo HC, corrección,
ajuste por ejercicio, clamp a 0, redondeo, y aviso de hipoglucemia.
"""

import pytest

from app.models import DiabeticProfile
from app.services.bolus import (
    BolusBreakdown,
    ExerciseLevel,
    TimeSlot,
    calculate_bolus,
)


def _profile(**overrides) -> DiabeticProfile:
    """Perfil base sensato. Sobrescribimos solo los campos del test."""
    base = dict(
        ration_grams=10,
        target_glucose=110,
        hypo_threshold=70,
        bolus_rounding_step=0.5,
        exercise_moderate_factor=-0.20,
        exercise_intense_factor=-0.40,
        ipr_breakfast=1.5,
        ipr_lunch=1.0,
        ipr_dinner=1.2,
        isf_breakfast=40,
        isf_lunch=50,
        isf_dinner=45,
    )
    base.update(overrides)
    return DiabeticProfile(**base)


# ===== Raciones =====


def test_rations_simple_division() -> None:
    """50 g HC con ración=10g → 5.0 raciones."""
    result = calculate_bolus(
        carbs_g=50,
        glucose_mg_dl=110,
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert result.rations == 5.0


def test_rations_one_decimal() -> None:
    """47 g HC → 4.7 raciones (no 5)."""
    result = calculate_bolus(
        carbs_g=47,
        glucose_mg_dl=110,
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert result.rations == 4.7


# ===== Bolo HC + selección de franja =====


@pytest.mark.parametrize(
    "slot,expected_carb",
    [
        (TimeSlot.BREAKFAST, 5.0 * 1.5),  # 7.5 U
        (TimeSlot.LUNCH, 5.0 * 1.0),      # 5.0 U
        (TimeSlot.DINNER, 5.0 * 1.2),     # 6.0 U
    ],
)
def test_bolus_carb_uses_slot_ipr(slot: TimeSlot, expected_carb: float) -> None:
    """El bolo de HC debe usar el IPR de la franja indicada."""
    result = calculate_bolus(
        carbs_g=50,
        glucose_mg_dl=110,  # = target → corrección = 0
        exercise=ExerciseLevel.NONE,
        slot=slot,
        profile=_profile(),
    )
    assert result.bolus_carb == expected_carb
    assert result.bolus_correction == 0.0


# ===== Corrección =====


def test_correction_positive_when_above_target() -> None:
    """Glucemia 160, target 110, ISF=50 → corrección = (160-110)/50 = 1.0 U."""
    result = calculate_bolus(
        carbs_g=0,
        glucose_mg_dl=160,
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert result.bolus_correction == 1.0


def test_correction_negative_when_below_target_reduces_bolus() -> None:
    """Glucemia 80, target 110, ISF=50 → corrección = -0.6 U.
    Bolo HC = 5 U, total pre-round = 4.4. La resta se aplica."""
    result = calculate_bolus(
        carbs_g=50,
        glucose_mg_dl=80,
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert result.bolus_correction == -0.6
    assert result.bolus_before_round == 4.4


def test_correction_cannot_drive_total_negative() -> None:
    """Caso extremo: la corrección negativa anularía el bolo. Total = 0."""
    result = calculate_bolus(
        carbs_g=10,            # bolo HC = 1 U
        glucose_mg_dl=40,      # muy baja → corrección = (40-110)/50 = -1.4 U
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert result.bolus_before_round == 0.0
    assert result.bolus_total == 0.0


# ===== Ejercicio =====


def test_moderate_exercise_reduces_bolus() -> None:
    """50g HC, glucemia=target, ejercicio moderado (-20%): 5.0 × 0.8 = 4.0 U."""
    result = calculate_bolus(
        carbs_g=50,
        glucose_mg_dl=110,
        exercise=ExerciseLevel.MODERATE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert result.exercise_factor == -0.20
    assert result.bolus_before_round == 4.0
    assert result.bolus_total == 4.0


def test_intense_exercise_reduces_bolus_more() -> None:
    """Ejercicio intenso (-40%): 5.0 × 0.6 = 3.0 U."""
    result = calculate_bolus(
        carbs_g=50,
        glucose_mg_dl=110,
        exercise=ExerciseLevel.INTENSE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert result.exercise_factor == -0.40
    assert result.bolus_before_round == 3.0


def test_custom_exercise_factors_are_used() -> None:
    """Si el usuario configura factores custom, se respetan."""
    result = calculate_bolus(
        carbs_g=50,
        glucose_mg_dl=110,
        exercise=ExerciseLevel.INTENSE,
        slot=TimeSlot.LUNCH,
        profile=_profile(exercise_intense_factor=-0.50),
    )
    assert result.exercise_factor == -0.50
    assert result.bolus_before_round == 2.5  # 5.0 × 0.5


# ===== Redondeo =====


@pytest.mark.parametrize(
    "step,expected",
    [
        (0.5, 3.0),   # 2.75 → 3.0 (half-up; banker's daría 2.5)
        (1.0, 3.0),   # 2.75 → 3
        (0.1, 2.8),   # 2.75 → 2.8 (half-up)
    ],
)
def test_rounding_step_half_up(step: float, expected: float) -> None:
    """Pre-round exacto de 2.75 U para verificar el comportamiento half-up.

    Construimos 2.75 = bolus_carb(2.0) + correction(0.75). Con IPR=1.0,
    ISF=20 y glucemia=125 (target=110): (125-110)/20 = 0.75.
    """
    result = calculate_bolus(
        carbs_g=20,
        glucose_mg_dl=125,
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(bolus_rounding_step=step, isf_lunch=20),
    )
    assert result.bolus_before_round == 2.75
    assert result.bolus_total == expected


# ===== Hipoglucemia =====


def test_hypoglycemia_warning_set_but_calculation_continues() -> None:
    """Por debajo del umbral, el flag se activa pero el cálculo sigue."""
    result = calculate_bolus(
        carbs_g=50,
        glucose_mg_dl=60,  # < 70
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert result.hypoglycemia_warning is True
    # El cálculo sigue: bolo HC=5, corr=(60-110)/50=-1, pre=4.0
    assert result.bolus_before_round == 4.0


def test_no_hypoglycemia_warning_at_threshold() -> None:
    """En el umbral exacto, no se considera hipoglucemia."""
    result = calculate_bolus(
        carbs_g=50,
        glucose_mg_dl=70,
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert result.hypoglycemia_warning is False


# ===== Configurabilidad de ración =====


def test_custom_ration_grams() -> None:
    """Algún usuario podría usar 12 g/ración (convención no española)."""
    result = calculate_bolus(
        carbs_g=60,
        glucose_mg_dl=110,
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(ration_grams=12),
    )
    assert result.rations == 5.0


# ===== Resultado dataclass =====


def test_result_is_immutable_breakdown() -> None:
    """`BolusBreakdown` es frozen — la UI lo recibe inmutable."""
    result = calculate_bolus(
        carbs_g=50,
        glucose_mg_dl=110,
        exercise=ExerciseLevel.NONE,
        slot=TimeSlot.LUNCH,
        profile=_profile(),
    )
    assert isinstance(result, BolusBreakdown)
    with pytest.raises(Exception):
        result.bolus_total = 99  # type: ignore[misc]
