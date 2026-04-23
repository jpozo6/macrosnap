"""Tests para los endpoints CRUD de comidas."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Meal, User


class TestListMeals:
    """Tests para GET /api/v1/meals."""

    def test_lista_vacia(self, client: TestClient) -> None:
        response = client.get("/api/v1/meals")
        assert response.status_code == 200
        assert response.json() == []

    def test_lista_con_comidas(self, client: TestClient, sample_meals: list[Meal]) -> None:
        response = client.get("/api/v1/meals")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_lista_con_limit(self, client: TestClient, sample_meals: list[Meal]) -> None:
        response = client.get("/api/v1/meals?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_lista_con_offset(self, client: TestClient, sample_meals: list[Meal]) -> None:
        response = client.get("/api/v1/meals?offset=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_filtro_por_fecha(self, client: TestClient, sample_meals: list[Meal]) -> None:
        response = client.get("/api/v1/meals?date_from=2026-04-09&date_to=2026-04-09")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestGetMeal:
    """Tests para GET /api/v1/meals/{meal_id}."""

    def test_get_meal_existente(self, client: TestClient, sample_meal: Meal) -> None:
        response = client.get(f"/api/v1/meals/{sample_meal.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["meal_name"] == "Arroz con pollo"
        assert data["macros"]["calories"] == 450.0
        assert len(data["foods"]) == 2

    def test_get_meal_no_existente(self, client: TestClient) -> None:
        response = client.get("/api/v1/meals/99999")
        assert response.status_code == 404
        assert "no encontrada" in response.json()["detail"].lower()


class TestDeleteMeal:
    """Tests para DELETE /api/v1/meals/{meal_id}."""

    def test_delete_meal_existente(self, client: TestClient, sample_meal: Meal) -> None:
        response = client.delete(f"/api/v1/meals/{sample_meal.id}")
        assert response.status_code == 204

        # Verificar que se eliminó
        response = client.get(f"/api/v1/meals/{sample_meal.id}")
        assert response.status_code == 404

    def test_delete_meal_no_existente(self, client: TestClient) -> None:
        response = client.delete("/api/v1/meals/99999")
        assert response.status_code == 404


class TestDailySummary:
    """Tests para GET /api/v1/meals/summary/daily."""

    def test_resumen_sin_comidas(self, client: TestClient) -> None:
        response = client.get("/api/v1/meals/summary/daily?date=2026-04-09")
        assert response.status_code == 200
        data = response.json()
        assert data["total_meals"] == 0
        assert data["macros"]["calories"] == 0

    def test_resumen_con_comidas(self, client: TestClient, sample_meals: list[Meal]) -> None:
        response = client.get("/api/v1/meals/summary/daily?date=2026-04-09")
        assert response.status_code == 200
        data = response.json()
        assert data["total_meals"] == 3
        assert data["macros"]["calories"] > 0

    def test_resumen_requiere_fecha(self, client: TestClient) -> None:
        response = client.get("/api/v1/meals/summary/daily")
        assert response.status_code == 422


class TestAuthIsolation:
    """Cada usuario solo ve sus propias comidas."""

    def test_meals_requiere_auth(self, anon_client: TestClient) -> None:
        response = anon_client.get("/api/v1/meals")
        assert response.status_code == 401

    def test_no_ve_meals_de_otro_usuario(
        self,
        client: TestClient,
        db_session: Session,
        sample_meal: Meal,
        other_user: User,
    ) -> None:
        # Comida del otro usuario en la BD
        otra = Meal(
            user_id=other_user.id, meal_name="No mía",
            calories=500, protein_g=10, carbs_g=10, fat_g=10, fiber_g=10,
        )
        db_session.add(otra)
        db_session.commit()

        response = client.get("/api/v1/meals")
        assert response.status_code == 200
        ids = [m["id"] for m in response.json()]
        assert sample_meal.id in ids
        assert otra.id not in ids

    def test_get_meal_de_otro_usuario_devuelve_404(
        self, client: TestClient, db_session: Session, other_user: User,
    ) -> None:
        otra = Meal(
            user_id=other_user.id, meal_name="Privada",
            calories=100, protein_g=1, carbs_g=1, fat_g=1, fiber_g=1,
        )
        db_session.add(otra)
        db_session.commit()
        db_session.refresh(otra)

        response = client.get(f"/api/v1/meals/{otra.id}")
        assert response.status_code == 404

    def test_delete_meal_de_otro_usuario_devuelve_404(
        self, client: TestClient, db_session: Session, other_user: User,
    ) -> None:
        otra = Meal(
            user_id=other_user.id, meal_name="Privada",
            calories=100, protein_g=1, carbs_g=1, fat_g=1, fiber_g=1,
        )
        db_session.add(otra)
        db_session.commit()
        db_session.refresh(otra)

        response = client.delete(f"/api/v1/meals/{otra.id}")
        assert response.status_code == 404
