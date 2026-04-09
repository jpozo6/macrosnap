"""Tests para los schemas Pydantic."""

import pytest
from pydantic import ValidationError

from app.schemas import (
    AnalysisResponse,
    DailySummaryResponse,
    FoodItem,
    MacroNutrients,
    MealResponse,
)


class TestMacroNutrients:
    """Tests para el schema MacroNutrients."""

    def test_valores_validos(self) -> None:
        macros = MacroNutrients(
            calories=450.0,
            protein_g=30.5,
            carbs_g=45.2,
            fat_g=15.8,
            fiber_g=5.3,
        )
        assert macros.calories == 450.0
        assert macros.protein_g == 30.5

    def test_valores_cero(self) -> None:
        macros = MacroNutrients(
            calories=0, protein_g=0, carbs_g=0, fat_g=0, fiber_g=0,
        )
        assert macros.calories == 0

    def test_valores_enteros_se_convierten_a_float(self) -> None:
        macros = MacroNutrients(
            calories=450, protein_g=30, carbs_g=45, fat_g=15, fiber_g=5,
        )
        assert isinstance(macros.calories, (int, float))

    def test_campo_faltante_falla(self) -> None:
        with pytest.raises(ValidationError):
            MacroNutrients(
                calories=450.0, protein_g=30.5, carbs_g=45.2,
                # fat_g y fiber_g faltan
            )


class TestFoodItem:
    """Tests para el schema FoodItem."""

    def test_food_completo(self) -> None:
        food = FoodItem(
            name="arroz blanco", confidence=0.95, amount=200, unit="g",
        )
        assert food.name == "arroz blanco"
        assert food.confidence == 0.95
        assert food.amount == 200
        assert food.unit == "g"

    def test_food_sin_porcion(self) -> None:
        food = FoodItem(name="manzana", confidence=0.8)
        assert food.amount is None
        assert food.unit is None

    def test_food_sin_nombre_falla(self) -> None:
        with pytest.raises(ValidationError):
            FoodItem(confidence=0.9)


class TestAnalysisResponse:
    """Tests para el schema AnalysisResponse."""

    def test_respuesta_completa(self) -> None:
        resp = AnalysisResponse(
            meal_id=1,
            meal_name="Ensalada",
            macros=MacroNutrients(
                calories=200, protein_g=10, carbs_g=20, fat_g=8, fiber_g=6,
            ),
            foods=[FoodItem(name="lechuga", confidence=0.9)],
        )
        assert resp.meal_id == 1
        assert resp.meal_name == "Ensalada"
        assert len(resp.foods) == 1

    def test_sin_foods_lista_vacia(self) -> None:
        resp = AnalysisResponse(
            meal_id=1,
            meal_name="Vacío",
            macros=MacroNutrients(
                calories=0, protein_g=0, carbs_g=0, fat_g=0, fiber_g=0,
            ),
            foods=[],
        )
        assert resp.foods == []


class TestDailySummaryResponse:
    """Tests para el schema DailySummaryResponse."""

    def test_resumen_diario(self) -> None:
        summary = DailySummaryResponse(
            date="2026-04-09",
            total_meals=3,
            macros=MacroNutrients(
                calories=1500, protein_g=80, carbs_g=150, fat_g=50, fiber_g=25,
            ),
        )
        assert summary.total_meals == 3
        assert summary.date == "2026-04-09"
