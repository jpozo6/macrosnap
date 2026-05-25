"""Router del perfil diabético y del cálculo de bolo de insulina."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import DiabeticProfile, User
from app.schemas import (
    BolusCalcRequest,
    BolusCalcResponse,
    DiabeticProfileOut,
    DiabeticProfileUpsert,
)
from app.services.bolus import calculate_bolus

router = APIRouter(prefix="/api/v1/diabetic-profile", tags=["diabetic-profile"])


def _get_profile_or_404(db: Session, user_id: int) -> DiabeticProfile:
    profile = (
        db.query(DiabeticProfile).filter(DiabeticProfile.user_id == user_id).first()
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil diabético no configurado.",
        )
    return profile


@router.get("", response_model=DiabeticProfileOut)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiabeticProfileOut:
    """Devuelve el perfil diabético del usuario autenticado."""
    profile = _get_profile_or_404(db, current_user.id)
    return DiabeticProfileOut.model_validate(profile)


@router.put("", response_model=DiabeticProfileOut)
def upsert_profile(
    payload: DiabeticProfileUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiabeticProfileOut:
    """Crea o actualiza el perfil diabético del usuario."""
    profile = (
        db.query(DiabeticProfile)
        .filter(DiabeticProfile.user_id == current_user.id)
        .first()
    )
    data = payload.model_dump()
    if profile:
        for field, value in data.items():
            setattr(profile, field, value)
    else:
        profile = DiabeticProfile(user_id=current_user.id, **data)
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return DiabeticProfileOut.model_validate(profile)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Elimina el perfil diabético (desactiva el modo diabético)."""
    profile = (
        db.query(DiabeticProfile)
        .filter(DiabeticProfile.user_id == current_user.id)
        .first()
    )
    if profile:
        db.delete(profile)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/calculate-bolus", response_model=BolusCalcResponse)
def calculate_bolus_endpoint(
    payload: BolusCalcRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BolusCalcResponse:
    """Calcula el bolo sugerido para la comida actual.

    No persiste nada — solo devuelve el desglose. La persistencia se hará
    al guardar la comida (PR 2: extensión de `meals`).
    """
    profile = _get_profile_or_404(db, current_user.id)
    result = calculate_bolus(
        carbs_g=payload.carbs_g,
        glucose_mg_dl=payload.glucose,
        exercise=payload.exercise,
        slot=payload.slot,
        profile=profile,
    )
    return BolusCalcResponse(
        rations=result.rations,
        bolus_carb=result.bolus_carb,
        bolus_correction=result.bolus_correction,
        exercise_factor=result.exercise_factor,
        bolus_before_round=result.bolus_before_round,
        bolus_total=result.bolus_total,
        hypoglycemia_warning=result.hypoglycemia_warning,
    )
