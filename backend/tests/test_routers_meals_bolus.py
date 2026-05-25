"""Tests del endpoint `PATCH /api/v1/meals/{meal_id}/bolus`."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import DiabeticProfile, Meal, User


def _bolus_payload(**overrides) -> dict:
    base = {
        "glucose": 140,
        "exercise": "none",
        "slot": "lunch",
        "bolus_chosen_units": 5.5,
    }
    base.update(overrides)
    return base


def _profile_data(**overrides) -> dict:
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


@pytest.fixture
def profile_for_user(db_session: Session, user: User) -> DiabeticProfile:
    """Perfil diabético del usuario por defecto (`client`)."""
    p = DiabeticProfile(user_id=user.id, **_profile_data())
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


class TestAuthAndOwnership:
    def test_sin_auth_401(self, anon_client: TestClient, sample_meal: Meal) -> None:
        r = anon_client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus", json=_bolus_payload()
        )
        assert r.status_code == 401

    def test_404_si_meal_no_existe(
        self, client: TestClient, profile_for_user: DiabeticProfile
    ) -> None:
        r = client.patch("/api/v1/meals/999999/bolus", json=_bolus_payload())
        assert r.status_code == 404

    def test_404_si_meal_de_otro_usuario(
        self,
        client: TestClient,
        profile_for_user: DiabeticProfile,
        db_session: Session,
        other_user: User,
    ) -> None:
        """No se debe poder PATCHear comidas de otro usuario."""
        foreign_meal = Meal(
            user_id=other_user.id,
            meal_name="Ajeno",
            calories=200,
            protein_g=10,
            carbs_g=30,
            fat_g=5,
            fiber_g=2,
        )
        db_session.add(foreign_meal)
        db_session.commit()
        r = client.patch(
            f"/api/v1/meals/{foreign_meal.id}/bolus", json=_bolus_payload()
        )
        assert r.status_code == 404


class TestRequiresDiabeticProfile:
    def test_404_si_usuario_no_tiene_perfil(
        self, client: TestClient, sample_meal: Meal
    ) -> None:
        """Sin perfil diabético no podemos calcular el desglose."""
        r = client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus", json=_bolus_payload()
        )
        assert r.status_code == 404
        assert "perfil" in r.json()["detail"].lower()


class TestHappyPath:
    def test_persiste_desglose_y_decision_del_usuario(
        self,
        client: TestClient,
        profile_for_user: DiabeticProfile,
        sample_meal: Meal,
        db_session: Session,
    ) -> None:
        """carbs_g=45.2, glucemia=140, lunch (IPR=1.0, ISF=50), sin ejercicio.
        raciones=4.5, bolo_HC=4.5, corr=(140-110)/50=0.6, total=5.1 → 5.0."""
        r = client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus",
            json=_bolus_payload(bolus_chosen_units=5.0),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["bolus"]["rations_hc"] == 4.5
        assert body["bolus"]["bolus_carb_units"] == 4.5
        assert body["bolus"]["bolus_correction_units"] == 0.6
        assert body["bolus"]["bolus_suggested_units"] == 5.0
        assert body["bolus"]["bolus_total_units"] == 5.0
        assert body["bolus"]["glucose_mg_dl"] == 140
        assert body["bolus"]["exercise_level"] == "none"
        assert body["bolus"]["slot"] == "lunch"

        db_session.refresh(sample_meal)
        assert sample_meal.bolus_total_units == 5.0
        assert sample_meal.rations_hc == 4.5

    def test_bolo_elegido_distinto_al_sugerido_se_respeta(
        self,
        client: TestClient,
        profile_for_user: DiabeticProfile,
        sample_meal: Meal,
    ) -> None:
        """Si el usuario decide pincharse menos de lo sugerido, se guarda."""
        r = client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus",
            json=_bolus_payload(bolus_chosen_units=3.0),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["bolus"]["bolus_suggested_units"] == 5.0
        assert body["bolus"]["bolus_total_units"] == 3.0

    def test_segundo_patch_sobrescribe(
        self,
        client: TestClient,
        profile_for_user: DiabeticProfile,
        sample_meal: Meal,
    ) -> None:
        """Idempotencia: re-PATCHear actualiza todos los campos."""
        client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus",
            json=_bolus_payload(glucose=140, bolus_chosen_units=5.0),
        )
        r = client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus",
            json=_bolus_payload(glucose=200, bolus_chosen_units=6.5),
        )
        body = r.json()
        assert body["bolus"]["glucose_mg_dl"] == 200
        assert body["bolus"]["bolus_total_units"] == 6.5

    def test_get_meal_devuelve_bolo(
        self,
        client: TestClient,
        profile_for_user: DiabeticProfile,
        sample_meal: Meal,
    ) -> None:
        """GET /meals/{id} expone el bloque `bolus` tras el PATCH."""
        client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus", json=_bolus_payload()
        )
        r = client.get(f"/api/v1/meals/{sample_meal.id}")
        assert r.status_code == 200
        assert r.json()["bolus"] is not None

    def test_meal_sin_bolo_devuelve_bolus_none(
        self, client: TestClient, sample_meal: Meal
    ) -> None:
        """Sin PATCH, el campo bolus debe ser explícitamente None."""
        r = client.get(f"/api/v1/meals/{sample_meal.id}")
        assert r.status_code == 200
        assert r.json()["bolus"] is None


class TestValidation:
    def test_rechaza_glucosa_fuera_de_rango(
        self,
        client: TestClient,
        profile_for_user: DiabeticProfile,
        sample_meal: Meal,
    ) -> None:
        r = client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus",
            json=_bolus_payload(glucose=10),
        )
        assert r.status_code == 422

    def test_rechaza_slot_invalido(
        self,
        client: TestClient,
        profile_for_user: DiabeticProfile,
        sample_meal: Meal,
    ) -> None:
        r = client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus",
            json=_bolus_payload(slot="snack"),
        )
        assert r.status_code == 422

    def test_rechaza_bolo_negativo(
        self,
        client: TestClient,
        profile_for_user: DiabeticProfile,
        sample_meal: Meal,
    ) -> None:
        r = client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus",
            json=_bolus_payload(bolus_chosen_units=-1),
        )
        assert r.status_code == 422

    def test_acepta_bolo_cero(
        self,
        client: TestClient,
        profile_for_user: DiabeticProfile,
        sample_meal: Meal,
    ) -> None:
        """El usuario puede decidir no pincharse (p. ej. hipo + bajos HC)."""
        r = client.patch(
            f"/api/v1/meals/{sample_meal.id}/bolus",
            json=_bolus_payload(bolus_chosen_units=0),
        )
        assert r.status_code == 200
        assert r.json()["bolus"]["bolus_total_units"] == 0
