"""Tests para el endpoint de análisis de imágenes."""

import io
import json
from unittest.mock import patch

from fastapi.testclient import TestClient


class TestAnalyzeImage:
    """Tests para POST /api/v1/analyze."""

    @patch("app.routers.analysis.analysis_graph")
    def test_analyze_image_ok(self, mock_graph: object, client: TestClient) -> None:
        mock_graph.invoke.return_value = {
            "identified_foods": [
                {"name": "arroz blanco", "confidence": 0.95},
                {"name": "pollo", "confidence": 0.92},
            ],
            "portions": [
                {"name": "arroz blanco", "amount": 200, "unit": "g"},
                {"name": "pollo", "amount": 150, "unit": "g"},
            ],
            "macros": {
                "calories": 450,
                "protein_g": 30.5,
                "carbs_g": 45.2,
                "fat_g": 15.8,
                "fiber_g": 5.3,
            },
            "meal_name": "Arroz con pollo",
            "error": None,
        }

        # Simular un archivo de imagen
        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0fake_jpeg_data")
        response = client.post(
            "/api/v1/analyze",
            files={"image": ("test.jpg", fake_image, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["meal_name"] == "Arroz con pollo"
        assert data["macros"]["calories"] == 450
        assert len(data["foods"]) == 2
        assert data["meal_id"] is not None

    @patch("app.routers.analysis.analysis_graph")
    def test_analyze_image_error_del_grafo(
        self, mock_graph: object, client: TestClient,
    ) -> None:
        mock_graph.invoke.return_value = {
            "identified_foods": [],
            "portions": [],
            "macros": {},
            "meal_name": "",
            "error": "Error identificando alimentos: timeout",
        }

        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0fake")
        response = client.post(
            "/api/v1/analyze",
            files={"image": ("test.jpg", fake_image, "image/jpeg")},
        )

        assert response.status_code == 422
        assert "error" in response.json()["detail"].lower()

    @patch("app.routers.analysis.analysis_graph")
    def test_analyze_image_excepcion_del_grafo(
        self, mock_graph: object, client: TestClient,
    ) -> None:
        mock_graph.invoke.side_effect = RuntimeError("Gemini API error")

        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0fake")
        response = client.post(
            "/api/v1/analyze",
            files={"image": ("test.jpg", fake_image, "image/jpeg")},
        )

        assert response.status_code == 500

    def test_analyze_sin_imagen_falla(self, client: TestClient) -> None:
        response = client.post("/api/v1/analyze")
        assert response.status_code == 422

    @patch("app.routers.analysis.analysis_graph")
    def test_analyze_guarda_en_db(self, mock_graph: object, client: TestClient) -> None:
        mock_graph.invoke.return_value = {
            "identified_foods": [{"name": "ensalada", "confidence": 0.9}],
            "portions": [{"name": "ensalada", "amount": 300, "unit": "g"}],
            "macros": {
                "calories": 150,
                "protein_g": 5,
                "carbs_g": 20,
                "fat_g": 7,
                "fiber_g": 8,
            },
            "meal_name": "Ensalada verde",
            "error": None,
        }

        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0fake")
        response = client.post(
            "/api/v1/analyze",
            files={"image": ("test.jpg", fake_image, "image/jpeg")},
        )

        assert response.status_code == 200
        meal_id = response.json()["meal_id"]

        # Verificar que se guardó en BD via el endpoint de meals
        get_response = client.get(f"/api/v1/meals/{meal_id}")
        assert get_response.status_code == 200
        assert get_response.json()["meal_name"] == "Ensalada verde"
