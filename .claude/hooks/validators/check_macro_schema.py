#!/usr/bin/env python3
"""Verifica consistencia del schema de macros entre schemas.py, state.py, models.py, prompts.py y nodes.py."""

import re
import sys
from pathlib import Path

CANONICAL_FIELDS = {"calories", "protein_g", "carbs_g", "fat_g", "fiber_g"}

FILES_TO_CHECK = {
    "backend/app/schemas.py": "MacroNutrients class",
    "backend/app/chain/state.py": "AnalysisState macros comment",
    "backend/app/models.py": "Meal model columns",
    "backend/app/chain/prompts.py": "CALCULATE_MACROS_PROMPT JSON structure",
    "backend/app/chain/nodes.py": "calculate_macros result keys",
}


def extract_macro_fields(filepath: str, content: str) -> set[str]:
    """Extrae los campos de macros según el tipo de archivo."""
    fields: set[str] = set()

    if "schemas.py" in filepath:
        # Buscar campos en MacroNutrients class
        in_class = False
        for line in content.split("\n"):
            if "class MacroNutrients" in line:
                in_class = True
                continue
            if in_class:
                if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    break
                match = re.match(r'\s+(\w+)\s*:', line)
                if match and not match.group(1).startswith("_"):
                    name = match.group(1)
                    if name not in ("model_config",):
                        fields.add(name)

    elif "models.py" in filepath:
        # Buscar columnas Float SOLO dentro de la clase Meal, no en otras
        # clases del fichero (p. ej. DiabeticProfile también tiene Float).
        meal_block = re.search(
            r'^class Meal\b.*?(?=^class\s|\Z)',
            content,
            re.DOTALL | re.MULTILINE,
        )
        scope = meal_block.group(0) if meal_block else ""
        for match in re.finditer(r'(\w+)\s*=\s*Column\(Float', scope):
            fields.add(match.group(1))

    elif "prompts.py" in filepath:
        # Buscar keys en el JSON de CALCULATE_MACROS_PROMPT
        prompt_match = re.search(
            r'CALCULATE_MACROS_PROMPT\s*=\s*"""(.*?)"""',
            content, re.DOTALL,
        )
        if prompt_match:
            for key_match in re.finditer(r'"(\w+)":\s*[\d.]', prompt_match.group(1)):
                fields.add(key_match.group(1))

    elif "nodes.py" in filepath:
        # Buscar keys solo dentro del dict "macros" en calculate_macros
        macros_block = re.search(
            r'"macros"\s*:\s*\{(.*?)\}', content, re.DOTALL,
        )
        if macros_block:
            for match in re.finditer(r'"(\w+)":\s*result\.get\(', macros_block.group(1)):
                fields.add(match.group(1))

    elif "state.py" in filepath:
        # Buscar en el comentario del campo macros
        comment_match = re.search(r'macros.*#\s*\{(.*?)\}', content)
        if comment_match:
            for field in re.finditer(r'(\w+)', comment_match.group(1)):
                fields.add(field.group(1))

    return fields


def main() -> int:
    errors: list[str] = []

    for filepath, description in FILES_TO_CHECK.items():
        path = Path(filepath)
        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8")
        fields = extract_macro_fields(filepath, content)

        if not fields:
            continue

        missing = CANONICAL_FIELDS - fields
        extra = fields - CANONICAL_FIELDS

        if missing:
            errors.append(f"  ⚠ {filepath} ({description}): faltan campos {missing}")
        if extra:
            errors.append(f"  ⚠ {filepath} ({description}): campos extra {extra}")

    if errors:
        print("❌ Inconsistencia en el schema de macronutrientes:")
        print("\n".join(errors))
        print(f"\nCampos canónicos: {CANONICAL_FIELDS}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
