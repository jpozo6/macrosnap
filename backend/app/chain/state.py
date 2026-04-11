"""Estado del grafo de análisis de macronutrientes."""

from typing import Optional, TypedDict


class AnalysisState(TypedDict):
    """Estado compartido entre los nodos del grafo LangGraph."""

    image_base64: str
    user_comment: str  # comentario del usuario sobre ingredientes/pesos
    identified_foods: list[dict]  # [{name, confidence}]
    portions: list[dict]  # [{name, amount, unit}]
    macros: dict  # {calories, protein_g, carbs_g, fat_g, fiber_g}
    meal_name: str  # nombre resumido del plato
    error: Optional[str]
