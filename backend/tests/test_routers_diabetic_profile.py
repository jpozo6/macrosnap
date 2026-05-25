"""Tests de los endpoints `/api/v1/diabetic-profile`."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import DiabeticProfile, User


def _valid_payload(**overrides) -> dict:
    base = {
        "ration_grams": 10,
        "target_glucose": 110,
        "hypo_threshold": 70,
        "bolus_rounding_step": 0.5,
        "exercise_moderate_factor": -0.20,
        "exercise_intense_factor": -0.40,
        "ipr_breakfast": 1.5,
        "ipr_lunch": 1.0,
        "ipr_dinner": 1.2,
        "isf_breakfast": 40,
        "isf_lunch": 50,
        "isf_dinner": 45,
    }
    base.update(overrides)
    return base


class TestAuthRequired:
    """Todos los endpoints exigen JWT válido."""

    def test_get_sin_auth_401(self, anon_client: TestClient) -> None:
        assert anon_client.get("/api/v1/diabetic-profile").status_code == 401

    def test_put_sin_auth_401(self, anon_client: TestClient) -> None:
        r = anon_client.put("/api/v1/diabetic-profile", json=_valid_payload())
        assert r.status_code == 401

    def test_delete_sin_auth_401(self, anon_client: TestClient) -> None:
        assert anon_client.delete("/api/v1/diabetic-profile").status_code == 401

    def test_calculate_sin_auth_401(self, anon_client: TestClient) -> None:
        r = anon_client.post(
            "/api/v1/diabetic-profile/calculate-bolus",
            json={"carbs_g": 50, "glucose": 110, "slot": "lunch"},
        )
        assert r.status_code == 401


class TestGetProfile:
    def test_404_si_no_existe(self, client: TestClient) -> None:
        r = client.get("/api/v1/diabetic-profile")
        assert r.status_code == 404

    def test_devuelve_perfil_tras_upsert(self, client: TestClient) -> None:
        client.put("/api/v1/diabetic-profile", json=_valid_payload())
        r = client.get("/api/v1/diabetic-profile")
        assert r.status_code == 200
        data = r.json()
        assert data["ipr_breakfast"] == 1.5
        assert data["isf_lunch"] == 50


class TestUpsertProfile:
    def test_crea_perfil_si_no_existe(
        self, client: TestClient, db_session: Session, user: User
    ) -> None:
        r = client.put("/api/v1/diabetic-profile", json=_valid_payload())
        assert r.status_code == 200
        profile = (
            db_session.query(DiabeticProfile)
            .filter(DiabeticProfile.user_id == user.id)
            .first()
        )
        assert profile is not None
        assert profile.ipr_breakfast == 1.5

    def test_actualiza_perfil_existente(self, client: TestClient) -> None:
        client.put("/api/v1/diabetic-profile", json=_valid_payload())
        r = client.put(
            "/api/v1/diabetic-profile", json=_valid_payload(ipr_breakfast=2.0)
        )
        assert r.status_code == 200
        assert r.json()["ipr_breakfast"] == 2.0

    def test_rechaza_rounding_step_invalido(self, client: TestClient) -> None:
        r = client.put(
            "/api/v1/diabetic-profile",
            json=_valid_payload(bolus_rounding_step=0.25),
        )
        assert r.status_code == 422

    def test_rechaza_target_fuera_de_rango(self, client: TestClient) -> None:
        r = client.put(
            "/api/v1/diabetic-profile", json=_valid_payload(target_glucose=50)
        )
        assert r.status_code == 422

    def test_rechaza_ipr_negativo(self, client: TestClient) -> None:
        r = client.put(
            "/api/v1/diabetic-profile", json=_valid_payload(ipr_breakfast=-1)
        )
        assert r.status_code == 422


class TestDeleteProfile:
    def test_elimina_perfil(
        self, client: TestClient, db_session: Session, user: User
    ) -> None:
        client.put("/api/v1/diabetic-profile", json=_valid_payload())
        r = client.delete("/api/v1/diabetic-profile")
        assert r.status_code == 204
        assert (
            db_session.query(DiabeticProfile)
            .filter(DiabeticProfile.user_id == user.id)
            .first()
            is None
        )

    def test_delete_sin_perfil_es_idempotente(self, client: TestClient) -> None:
        """Borrar cuando no hay perfil no debe romper — útil para 'desactivar' modo diabético."""
        r = client.delete("/api/v1/diabetic-profile")
        assert r.status_code == 204


class TestCalculateBolus:
    def test_404_si_no_hay_perfil(self, client: TestClient) -> None:
        r = client.post(
            "/api/v1/diabetic-profile/calculate-bolus",
            json={"carbs_g": 50, "glucose": 110, "slot": "lunch"},
        )
        assert r.status_code == 404

    def test_calculo_basico_devuelve_desglose(self, client: TestClient) -> None:
        client.put("/api/v1/diabetic-profile", json=_valid_payload())
        r = client.post(
            "/api/v1/diabetic-profile/calculate-bolus",
            json={
                "carbs_g": 50,
                "glucose": 110,
                "exercise": "none",
                "slot": "lunch",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["rations"] == 5.0
        assert data["bolus_carb"] == 5.0
        assert data["bolus_correction"] == 0.0
        assert data["bolus_total"] == 5.0
        assert data["hypoglycemia_warning"] is False

    def test_calculo_marca_hipoglucemia(self, client: TestClient) -> None:
        client.put("/api/v1/diabetic-profile", json=_valid_payload())
        r = client.post(
            "/api/v1/diabetic-profile/calculate-bolus",
            json={"carbs_g": 50, "glucose": 60, "exercise": "none", "slot": "lunch"},
        )
        assert r.status_code == 200
        assert r.json()["hypoglycemia_warning"] is True

    def test_slot_invalido_422(self, client: TestClient) -> None:
        client.put("/api/v1/diabetic-profile", json=_valid_payload())
        r = client.post(
            "/api/v1/diabetic-profile/calculate-bolus",
            json={"carbs_g": 50, "glucose": 110, "slot": "midnight"},
        )
        assert r.status_code == 422

    def test_glucosa_fuera_de_rango_422(self, client: TestClient) -> None:
        client.put("/api/v1/diabetic-profile", json=_valid_payload())
        r = client.post(
            "/api/v1/diabetic-profile/calculate-bolus",
            json={"carbs_g": 50, "glucose": 10, "slot": "lunch"},
        )
        assert r.status_code == 422
