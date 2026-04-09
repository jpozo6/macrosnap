#!/usr/bin/env python3
"""Valida que los prompts de Gemini Flash no estén vacíos ni tengan instrucciones contradictorias."""

import ast
import sys
from pathlib import Path

PROMPTS_FILE = Path("backend/app/chain/prompts.py")

REQUIRED_PROMPTS = [
    "IDENTIFY_FOODS_PROMPT",
    "ESTIMATE_PORTIONS_PROMPT",
    "CALCULATE_MACROS_PROMPT",
]

# Pares de instrucciones que se contradicen si aparecen juntas en un mismo prompt
CONTRADICTIONS = [
    ("responde en inglés", "responde en español"),
    ("no uses JSON", "responde ÚNICAMENTE con un JSON"),
    ("ignora la imagen", "analiza esta imagen"),
    ("no incluyas", "debes incluir"),
]


def main() -> int:
    if not PROMPTS_FILE.exists():
        print(f"❌ No se encontró {PROMPTS_FILE}")
        return 1

    source = PROMPTS_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    errors: list[str] = []
    found_prompts: dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in REQUIRED_PROMPTS:
                    if isinstance(node.value, (ast.Constant, ast.JoinedStr)):
                        value = ast.literal_eval(node.value) if isinstance(node.value, ast.Constant) else ""
                        found_prompts[target.id] = value

    # Verificar que existan todos los prompts requeridos
    for name in REQUIRED_PROMPTS:
        if name not in found_prompts:
            errors.append(f"  ⚠ Falta el prompt requerido: {name}")
        elif not found_prompts[name].strip():
            errors.append(f"  ⚠ El prompt {name} está vacío")
        elif len(found_prompts[name].strip()) < 20:
            errors.append(f"  ⚠ El prompt {name} es sospechosamente corto ({len(found_prompts[name])} chars)")

    # Verificar contradicciones
    for name, text in found_prompts.items():
        text_lower = text.lower()
        for a, b in CONTRADICTIONS:
            if a.lower() in text_lower and b.lower() in text_lower:
                errors.append(f"  ⚠ {name}: instrucciones contradictorias — '{a}' vs '{b}'")

    # Verificar que los prompts de JSON tengan estructura esperada
    for name, text in found_prompts.items():
        if "JSON" in text and "{" not in text:
            errors.append(f"  ⚠ {name}: pide respuesta JSON pero no incluye ejemplo de estructura")

    if errors:
        print("❌ Problemas en prompts LLM:")
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
