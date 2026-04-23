"""Router para el endpoint de análisis de imágenes."""

import base64
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.chain.graph import analysis_graph
from app.db import get_db
from app.dependencies import get_current_user
from app.models import Meal, User
from app.schemas import AnalysisResponse, FoodItem, MacroNutrients

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    image: UploadFile = File(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    """Recibe una imagen de comida, analiza macronutrientes y guarda en DB."""
    contents = await image.read()
    image_base64 = base64.b64encode(contents).decode("utf-8")

    initial_state = {
        "image_base64": image_base64,
        "user_comment": comment.strip(),
        "identified_foods": [],
        "portions": [],
        "macros": {},
        "meal_name": "",
        "error": None,
    }

    try:
        result = analysis_graph.invoke(initial_state)
    except Exception as e:
        logger.error("Error ejecutando el grafo de análisis: %s", e)
        raise HTTPException(status_code=500, detail=f"Error en el análisis: {e}")

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    # Combinar foods identificados con porciones
    foods_combined = []
    portions_map = {p["name"]: p for p in result.get("portions", [])}
    for food in result.get("identified_foods", []):
        portion = portions_map.get(food["name"], {})
        foods_combined.append({
            "name": food["name"],
            "confidence": food["confidence"],
            "amount": portion.get("amount"),
            "unit": portion.get("unit"),
        })

    macros = result.get("macros", {})

    # Guardar en DB
    meal = Meal(
        user_id=current_user.id,
        meal_name=result.get("meal_name", "Comida"),
        calories=macros.get("calories", 0),
        protein_g=macros.get("protein_g", 0),
        carbs_g=macros.get("carbs_g", 0),
        fat_g=macros.get("fat_g", 0),
        fiber_g=macros.get("fiber_g", 0),
        image_base64=image_base64,
    )
    meal.foods = foods_combined
    db.add(meal)
    db.commit()
    db.refresh(meal)

    return AnalysisResponse(
        meal_id=meal.id,
        meal_name=meal.meal_name,
        macros=MacroNutrients(**macros),
        foods=[FoodItem(**f) for f in foods_combined],
    )
