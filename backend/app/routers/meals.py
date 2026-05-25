"""Router para el CRUD de comidas (histórico)."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import DiabeticProfile, Meal, User
from app.schemas import (
    BolusData,
    DailySummaryResponse,
    FoodItem,
    MacroNutrients,
    MealBolusPatch,
    MealResponse,
)
from app.services.bolus import calculate_bolus

router = APIRouter(prefix="/api/v1/meals", tags=["meals"])


def _meal_bolus_data(meal: Meal) -> BolusData | None:
    """Devuelve el sub-objeto de bolo si la comida lo tiene registrado."""
    if meal.bolus_total_units is None:
        return None
    return BolusData(
        glucose_mg_dl=meal.glucose_mg_dl,
        exercise_level=meal.exercise_level,
        slot=meal.slot,
        rations_hc=meal.rations_hc,
        bolus_carb_units=meal.bolus_carb_units,
        bolus_correction_units=meal.bolus_correction_units,
        bolus_suggested_units=meal.bolus_suggested_units,
        bolus_total_units=meal.bolus_total_units,
    )


def _meal_to_response(meal: Meal) -> MealResponse:
    """Convierte un modelo Meal a su schema de respuesta."""
    return MealResponse(
        id=meal.id,
        meal_name=meal.meal_name,
        macros=MacroNutrients(
            calories=meal.calories,
            protein_g=meal.protein_g,
            carbs_g=meal.carbs_g,
            fat_g=meal.fat_g,
            fiber_g=meal.fiber_g,
        ),
        foods=[FoodItem(**f) for f in meal.foods],
        image_base64=meal.image_base64,
        created_at=meal.created_at,
        bolus=_meal_bolus_data(meal),
    )


@router.get("", response_model=list[MealResponse])
def list_meals(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MealResponse]:
    """Lista las comidas del usuario autenticado con filtros opcionales."""
    query = db.query(Meal).filter(Meal.user_id == current_user.id)

    if date_from:
        query = query.filter(
            Meal.created_at >= datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc)
        )
    if date_to:
        next_day = datetime(date_to.year, date_to.month, date_to.day, tzinfo=timezone.utc)
        next_day = next_day.replace(hour=23, minute=59, second=59)
        query = query.filter(Meal.created_at <= next_day)

    meals = query.order_by(Meal.created_at.desc()).offset(offset).limit(limit).all()
    return [_meal_to_response(m) for m in meals]


@router.get("/summary/daily", response_model=DailySummaryResponse)
def daily_summary(
    date: date = Query(..., description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailySummaryResponse:
    """Devuelve el resumen diario de macronutrientes del usuario autenticado."""
    start = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
    end = start.replace(hour=23, minute=59, second=59)

    result = db.query(
        func.count(Meal.id).label("total"),
        func.coalesce(func.sum(Meal.calories), 0).label("calories"),
        func.coalesce(func.sum(Meal.protein_g), 0).label("protein_g"),
        func.coalesce(func.sum(Meal.carbs_g), 0).label("carbs_g"),
        func.coalesce(func.sum(Meal.fat_g), 0).label("fat_g"),
        func.coalesce(func.sum(Meal.fiber_g), 0).label("fiber_g"),
    ).filter(
        Meal.user_id == current_user.id,
        Meal.created_at >= start,
        Meal.created_at <= end,
    ).one()

    return DailySummaryResponse(
        date=date.isoformat(),
        total_meals=result.total,
        macros=MacroNutrients(
            calories=result.calories,
            protein_g=result.protein_g,
            carbs_g=result.carbs_g,
            fat_g=result.fat_g,
            fiber_g=result.fiber_g,
        ),
    )


@router.get("/{meal_id}", response_model=MealResponse)
def get_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealResponse:
    """Obtiene el detalle de una comida del usuario autenticado."""
    meal = db.query(Meal).filter(
        Meal.id == meal_id, Meal.user_id == current_user.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Comida no encontrada")
    return _meal_to_response(meal)


@router.delete("/{meal_id}", status_code=204)
def delete_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Elimina una comida del histórico del usuario autenticado."""
    meal = db.query(Meal).filter(
        Meal.id == meal_id, Meal.user_id == current_user.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Comida no encontrada")
    db.delete(meal)
    db.commit()


@router.patch("/{meal_id}/bolus", response_model=MealResponse)
def set_meal_bolus(
    meal_id: int,
    payload: MealBolusPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealResponse:
    """Registra el bolo de insulina de una comida.

    El servidor recalcula el desglose con `calculate_bolus(...)` usando los
    `carbs_g` de la comida y el perfil clínico vigente — la única cifra del
    cliente que persistimos tal cual es `bolus_chosen_units`, lo que el
    usuario decidió administrarse (puede diferir del sugerido).

    Idempotente: una segunda llamada sobrescribe los valores anteriores.
    """
    meal = (
        db.query(Meal)
        .filter(Meal.id == meal_id, Meal.user_id == current_user.id)
        .first()
    )
    if not meal:
        raise HTTPException(status_code=404, detail="Comida no encontrada")

    profile = (
        db.query(DiabeticProfile)
        .filter(DiabeticProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=404, detail="Perfil diabético no configurado."
        )

    breakdown = calculate_bolus(
        carbs_g=meal.carbs_g,
        glucose_mg_dl=payload.glucose,
        exercise=payload.exercise,
        slot=payload.slot,
        profile=profile,
    )

    meal.glucose_mg_dl = payload.glucose
    meal.exercise_level = payload.exercise.value
    meal.slot = payload.slot.value
    meal.rations_hc = breakdown.rations
    meal.bolus_carb_units = breakdown.bolus_carb
    meal.bolus_correction_units = breakdown.bolus_correction
    meal.bolus_suggested_units = breakdown.bolus_total
    meal.bolus_total_units = payload.bolus_chosen_units

    db.commit()
    db.refresh(meal)
    return _meal_to_response(meal)
