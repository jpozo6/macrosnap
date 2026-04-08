"""Router para el CRUD de comidas (histórico)."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Meal
from app.schemas import DailySummaryResponse, FoodItem, MacroNutrients, MealResponse

router = APIRouter(prefix="/api/v1/meals", tags=["meals"])


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
    )


@router.get("", response_model=list[MealResponse])
def list_meals(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[MealResponse]:
    """Lista las comidas del histórico con filtros opcionales."""
    query = db.query(Meal)

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
) -> DailySummaryResponse:
    """Devuelve el resumen diario de macronutrientes."""
    start = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
    end = start.replace(hour=23, minute=59, second=59)

    result = db.query(
        func.count(Meal.id).label("total"),
        func.coalesce(func.sum(Meal.calories), 0).label("calories"),
        func.coalesce(func.sum(Meal.protein_g), 0).label("protein_g"),
        func.coalesce(func.sum(Meal.carbs_g), 0).label("carbs_g"),
        func.coalesce(func.sum(Meal.fat_g), 0).label("fat_g"),
        func.coalesce(func.sum(Meal.fiber_g), 0).label("fiber_g"),
    ).filter(Meal.created_at >= start, Meal.created_at <= end).one()

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
) -> MealResponse:
    """Obtiene el detalle de una comida."""
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Comida no encontrada")
    return _meal_to_response(meal)


@router.delete("/{meal_id}", status_code=204)
def delete_meal(
    meal_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Elimina una comida del histórico."""
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Comida no encontrada")
    db.delete(meal)
    db.commit()
