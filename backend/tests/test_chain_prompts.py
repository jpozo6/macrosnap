"""Tests para los templates de prompts."""

from app.chain.prompts import (
    CALCULATE_MACROS_PROMPT,
    ESTIMATE_PORTIONS_PROMPT,
    IDENTIFY_FOODS_PROMPT,
)


class TestPrompts:
    """Tests para verificar que los prompts están bien formados."""

    def test_identify_foods_no_vacio(self) -> None:
        assert len(IDENTIFY_FOODS_PROMPT.strip()) > 50

    def test_estimate_portions_no_vacio(self) -> None:
        assert len(ESTIMATE_PORTIONS_PROMPT.strip()) > 50

    def test_calculate_macros_no_vacio(self) -> None:
        assert len(CALCULATE_MACROS_PROMPT.strip()) > 50

    def test_identify_foods_pide_json(self) -> None:
        assert "JSON" in IDENTIFY_FOODS_PROMPT
        assert "foods" in IDENTIFY_FOODS_PROMPT

    def test_estimate_portions_tiene_placeholder(self) -> None:
        assert "{foods_list}" in ESTIMATE_PORTIONS_PROMPT

    def test_calculate_macros_tiene_placeholder(self) -> None:
        assert "{portions_list}" in CALCULATE_MACROS_PROMPT

    def test_calculate_macros_incluye_todos_los_campos(self) -> None:
        for field in ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g"]:
            assert field in CALCULATE_MACROS_PROMPT, f"Falta {field} en CALCULATE_MACROS_PROMPT"

    def test_estimate_portions_se_puede_formatear(self) -> None:
        formatted = ESTIMATE_PORTIONS_PROMPT.format(foods_list="- arroz\n- pollo", user_comment_section="")
        assert "arroz" in formatted
        assert "pollo" in formatted

    def test_calculate_macros_se_puede_formatear(self) -> None:
        formatted = CALCULATE_MACROS_PROMPT.format(portions_list="- arroz: 200 g")
        assert "arroz" in formatted
