"""Tests para los nodos del grafo y el parser de respuestas."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.chain.nodes import (
    _parse_json_response,
    calculate_macros,
    estimate_portions,
    identify_foods,
)


class TestParseJsonResponse:
    """Tests para el parser de respuestas JSON del LLM."""

    def test_json_limpio(self) -> None:
        result = _parse_json_response('{"calories": 450}')
        assert result == {"calories": 450}

    def test_json_con_code_block(self) -> None:
        text = '```json\n{"calories": 450}\n```'
        result = _parse_json_response(text)
        assert result == {"calories": 450}

    def test_json_con_code_block_sin_lenguaje(self) -> None:
        text = '```\n{"calories": 300}\n```'
        result = _parse_json_response(text)
        assert result == {"calories": 300}

    def test_json_con_whitespace(self) -> None:
        text = '\n\n  {"calories": 450}  \n\n'
        result = _parse_json_response(text)
        assert result == {"calories": 450}

    def test_json_truncado_falla(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            _parse_json_response('{"calories": 450, "protein_g":')

    def test_texto_plano_falla(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            _parse_json_response("No puedo analizar esta imagen.")

    def test_json_complejo(self) -> None:
        text = json.dumps({
            "foods": [
                {"name": "arroz blanco", "confidence": 0.95},
                {"name": "pollo", "confidence": 0.92},
            ],
            "meal_name": "Arroz con pollo",
        })
        result = _parse_json_response(text)
        assert len(result["foods"]) == 2
        assert result["meal_name"] == "Arroz con pollo"

    def test_json_vacio(self) -> None:
        result = _parse_json_response("{}")
        assert result == {}


class TestIdentifyFoods:
    """Tests para el nodo identify_foods."""

    @patch("app.chain.nodes.get_llm")
    def test_identify_foods_ok(self, mock_get_llm: MagicMock) -> None:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content=json.dumps({
                "foods": [{"name": "arroz blanco", "confidence": 0.95}],
                "meal_name": "Arroz",
            })
        )
        mock_get_llm.return_value = mock_llm

        state = {
            "image_base64": "fake_base64_data",
            "identified_foods": [],
            "portions": [],
            "macros": {},
            "meal_name": "",
            "error": None,
        }

        result = identify_foods(state)
        assert result["identified_foods"] == [{"name": "arroz blanco", "confidence": 0.95}]
        assert result["meal_name"] == "Arroz"

    @patch("app.chain.nodes.get_llm")
    def test_identify_foods_error_retorna_error(self, mock_get_llm: MagicMock) -> None:
        mock_get_llm.side_effect = RuntimeError("API key missing")

        state = {
            "image_base64": "fake",
            "identified_foods": [],
            "portions": [],
            "macros": {},
            "meal_name": "",
            "error": None,
        }

        result = identify_foods(state)
        assert "error" in result
        assert "Error identificando alimentos" in result["error"]

    @patch("app.chain.nodes.get_llm")
    def test_identify_foods_respuesta_vacia(self, mock_get_llm: MagicMock) -> None:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"foods": [], "meal_name": "No identificado"}'
        )
        mock_get_llm.return_value = mock_llm

        state = {
            "image_base64": "fake",
            "identified_foods": [],
            "portions": [],
            "macros": {},
            "meal_name": "",
            "error": None,
        }

        result = identify_foods(state)
        assert result["identified_foods"] == []
        assert result["meal_name"] == "No identificado"


class TestEstimatePortions:
    """Tests para el nodo estimate_portions."""

    @patch("app.chain.nodes.get_llm")
    def test_estimate_portions_ok(self, mock_get_llm: MagicMock) -> None:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content=json.dumps({
                "portions": [{"name": "arroz blanco", "amount": 200, "unit": "g"}],
            })
        )
        mock_get_llm.return_value = mock_llm

        state = {
            "image_base64": "fake",
            "identified_foods": [{"name": "arroz blanco", "confidence": 0.95}],
            "portions": [],
            "macros": {},
            "meal_name": "Arroz",
            "error": None,
        }

        result = estimate_portions(state)
        assert result["portions"] == [{"name": "arroz blanco", "amount": 200, "unit": "g"}]

    def test_estimate_portions_con_error_previo(self) -> None:
        state = {
            "image_base64": "fake",
            "identified_foods": [],
            "portions": [],
            "macros": {},
            "meal_name": "",
            "error": "Error previo",
        }

        result = estimate_portions(state)
        assert result == {}


class TestCalculateMacros:
    """Tests para el nodo calculate_macros."""

    @patch("app.chain.nodes.get_llm")
    def test_calculate_macros_ok(self, mock_get_llm: MagicMock) -> None:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content=json.dumps({
                "calories": 450,
                "protein_g": 30.5,
                "carbs_g": 45.2,
                "fat_g": 15.8,
                "fiber_g": 5.3,
            })
        )
        mock_get_llm.return_value = mock_llm

        state = {
            "image_base64": "fake",
            "identified_foods": [{"name": "arroz", "confidence": 0.95}],
            "portions": [{"name": "arroz", "amount": 200, "unit": "g"}],
            "macros": {},
            "meal_name": "Arroz",
            "error": None,
        }

        result = calculate_macros(state)
        assert result["macros"]["calories"] == 450
        assert result["macros"]["protein_g"] == 30.5
        assert result["macros"]["fiber_g"] == 5.3

    def test_calculate_macros_con_error_previo(self) -> None:
        state = {
            "image_base64": "fake",
            "identified_foods": [],
            "portions": [],
            "macros": {},
            "meal_name": "",
            "error": "Error previo",
        }

        result = calculate_macros(state)
        assert result == {}

    @patch("app.chain.nodes.get_llm")
    def test_calculate_macros_campos_faltantes_default_cero(
        self, mock_get_llm: MagicMock,
    ) -> None:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"calories": 200}'
        )
        mock_get_llm.return_value = mock_llm

        state = {
            "image_base64": "fake",
            "identified_foods": [],
            "portions": [{"name": "algo", "amount": 100, "unit": "g"}],
            "macros": {},
            "meal_name": "Algo",
            "error": None,
        }

        result = calculate_macros(state)
        assert result["macros"]["calories"] == 200
        assert result["macros"]["protein_g"] == 0
        assert result["macros"]["fiber_g"] == 0
