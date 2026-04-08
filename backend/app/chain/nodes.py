"""Nodos del grafo LangGraph para análisis de macronutrientes."""

import base64
import json
import logging

from langchain_core.messages import HumanMessage

from app.chain.prompts import (
    CALCULATE_MACROS_PROMPT,
    ESTIMATE_PORTIONS_PROMPT,
    IDENTIFY_FOODS_PROMPT,
)
from app.chain.state import AnalysisState
from app.services.llm import get_llm

logger = logging.getLogger(__name__)


def _parse_json_response(text: str) -> dict:
    """Extrae y parsea JSON de la respuesta del LLM."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:])
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


def identify_foods(state: AnalysisState) -> dict:
    """Nodo 1: Identifica los alimentos en la imagen usando visión multimodal."""
    try:
        llm = get_llm()
        image_data = state["image_base64"]

        message = HumanMessage(
            content=[
                {"type": "text", "text": IDENTIFY_FOODS_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                },
            ]
        )

        response = llm.invoke([message])
        result = _parse_json_response(response.content)

        return {
            "identified_foods": result.get("foods", []),
            "meal_name": result.get("meal_name", "Comida no identificada"),
        }
    except Exception as e:
        logger.error("Error en identify_foods: %s", e)
        return {"error": f"Error identificando alimentos: {e}"}


def estimate_portions(state: AnalysisState) -> dict:
    """Nodo 2: Estima las porciones de cada alimento identificado."""
    if state.get("error"):
        return {}

    try:
        llm = get_llm()
        foods_list = "\n".join(
            f"- {f['name']} (confianza: {f['confidence']})"
            for f in state["identified_foods"]
        )

        prompt = ESTIMATE_PORTIONS_PROMPT.format(foods_list=foods_list)
        response = llm.invoke([HumanMessage(content=prompt)])
        result = _parse_json_response(response.content)

        return {"portions": result.get("portions", [])}
    except Exception as e:
        logger.error("Error en estimate_portions: %s", e)
        return {"error": f"Error estimando porciones: {e}"}


def calculate_macros(state: AnalysisState) -> dict:
    """Nodo 3: Calcula los macronutrientes totales de la comida."""
    if state.get("error"):
        return {}

    try:
        llm = get_llm()
        portions_list = "\n".join(
            f"- {p['name']}: {p['amount']} {p['unit']}" for p in state["portions"]
        )

        prompt = CALCULATE_MACROS_PROMPT.format(portions_list=portions_list)
        response = llm.invoke([HumanMessage(content=prompt)])
        result = _parse_json_response(response.content)

        return {
            "macros": {
                "calories": result.get("calories", 0),
                "protein_g": result.get("protein_g", 0),
                "carbs_g": result.get("carbs_g", 0),
                "fat_g": result.get("fat_g", 0),
                "fiber_g": result.get("fiber_g", 0),
            }
        }
    except Exception as e:
        logger.error("Error en calculate_macros: %s", e)
        return {"error": f"Error calculando macros: {e}"}
