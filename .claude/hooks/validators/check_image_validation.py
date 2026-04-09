#!/usr/bin/env python3
"""Verifica que exista validación de imágenes antes de enviarlas al modelo."""

import re
import sys
from pathlib import Path

ANALYSIS_ROUTER = Path("backend/app/routers/analysis.py")

REQUIRED_CHECKS = {
    "formato": [
        r"content.type",
        r"content_type",
        r"image/(jpeg|png|webp)",
        r"\.(jpg|jpeg|png|webp)",
        r"ALLOWED_.*TYPES",
        r"allowed.*formats",
    ],
    "tamaño": [
        r"MAX.*SIZE",
        r"max.*size",
        r"file.*size",
        r"content.*length",
        r"len\(contents\)",
        r"too.*large",
    ],
}


def main() -> int:
    if not ANALYSIS_ROUTER.exists():
        print(f"❌ No se encontró {ANALYSIS_ROUTER}")
        return 1

    content = ANALYSIS_ROUTER.read_text(encoding="utf-8")
    errors: list[str] = []

    for check_name, patterns in REQUIRED_CHECKS.items():
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        if not found:
            errors.append(f"  ⚠ No se detectó validación de {check_name} de imagen en {ANALYSIS_ROUTER}")

    if errors:
        print("❌ Falta validación de imágenes en el pipeline de análisis:")
        print("\n".join(errors))
        print("\nSe recomienda validar formato (JPEG/PNG/WebP) y tamaño máximo antes de enviar al modelo.")
        print("Ejemplo: rechazar archivos >10MB y formatos no soportados.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
