#!/usr/bin/env python3
"""Ejecuta tests rápidos del parser de respuestas de Gemini Flash."""

import json
import sys
from pathlib import Path

# Simulamos el parser que está en nodes.py
def parse_json_response(text: str) -> dict:
    """Replica la lógica de _parse_json_response de nodes.py."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:])
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


# Casos de prueba que cubren respuestas reales de Gemini Flash
TEST_CASES = [
    # Caso 1: JSON limpio
    {
        "input": '{"calories": 450, "protein_g": 30.5, "carbs_g": 45.2, "fat_g": 15.8, "fiber_g": 5.3}',
        "should_parse": True,
        "description": "JSON limpio",
    },
    # Caso 2: JSON con markdown code block
    {
        "input": '```json\n{"calories": 450, "protein_g": 30.5, "carbs_g": 45.2, "fat_g": 15.8, "fiber_g": 5.3}\n```',
        "should_parse": True,
        "description": "JSON con code block markdown",
    },
    # Caso 3: JSON con whitespace extra
    {
        "input": '\n\n  {"calories": 450, "protein_g": 30.5, "carbs_g": 45.2, "fat_g": 15.8, "fiber_g": 5.3}  \n\n',
        "should_parse": True,
        "description": "JSON con whitespace",
    },
    # Caso 4: JSON vacío (respuesta alucinada)
    {
        "input": "{}",
        "should_parse": True,
        "description": "JSON vacío (alucinación)",
    },
    # Caso 5: Texto plano sin JSON
    {
        "input": "No puedo analizar esta imagen porque no contiene comida.",
        "should_parse": False,
        "description": "Texto plano sin JSON",
    },
    # Caso 6: JSON parcial/truncado
    {
        "input": '{"calories": 450, "protein_g": 30.5, "carbs_g":',
        "should_parse": False,
        "description": "JSON truncado",
    },
    # Caso 7: Foods response
    {
        "input": '{"foods": [{"name": "arroz blanco", "confidence": 0.95}], "meal_name": "Arroz con pollo"}',
        "should_parse": True,
        "description": "Respuesta de identificación de alimentos",
    },
    # Caso 8: Code block sin especificar lenguaje
    {
        "input": '```\n{"calories": 300}\n```',
        "should_parse": True,
        "description": "Code block sin lenguaje",
    },
]


def main() -> int:
    errors: list[str] = []
    passed = 0

    for i, case in enumerate(TEST_CASES, 1):
        try:
            result = parse_json_response(case["input"])
            if not case["should_parse"]:
                errors.append(f"  ✗ Caso {i} ({case['description']}): debería fallar pero parseó OK")
            else:
                passed += 1
        except (json.JSONDecodeError, ValueError, KeyError):
            if case["should_parse"]:
                errors.append(f"  ✗ Caso {i} ({case['description']}): debería parsear pero falló")
            else:
                passed += 1

    if errors:
        print(f"❌ Tests de parsing fallidos ({passed}/{len(TEST_CASES)} pasaron):")
        print("\n".join(errors))
        return 1

    print(f"✓ Todos los tests de parsing pasaron ({passed}/{len(TEST_CASES)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
