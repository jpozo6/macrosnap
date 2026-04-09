#!/usr/bin/env python3
"""Detecta valores nutricionales absurdos en tests, fixtures y código."""

import re
import sys
from pathlib import Path

# Rangos razonables por comida individual
RANGES = {
    "calories": (0, 5000),
    "protein_g": (0, 500),
    "carbs_g": (0, 1000),
    "fat_g": (0, 500),
    "fiber_g": (0, 200),
}

# Archivos a escanear (tests, fixtures, seeds, examples)
SCAN_DIRS = [
    Path("backend/tests"),
    Path("backend/app"),
    Path("mobile/src"),
]

SCAN_EXTENSIONS = {".py", ".json", ".ts", ".tsx"}


def scan_file(filepath: Path) -> list[str]:
    """Escanea un archivo buscando valores de macros fuera de rango."""
    issues: list[str] = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return []

    for field, (min_val, max_val) in RANGES.items():
        # Patrón: "field": valor o field=valor o "field": valor
        patterns = [
            rf'["\']?{field}["\']?\s*[:=]\s*(-?[\d.]+)',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                try:
                    value = float(match.group(1))
                    if value < min_val or value > max_val:
                        line_num = content[:match.start()].count("\n") + 1
                        issues.append(
                            f"  ⚠ {filepath}:{line_num} — {field}={value} "
                            f"fuera de rango razonable [{min_val}, {max_val}]"
                        )
                except ValueError:
                    continue

    return issues


def main() -> int:
    all_issues: list[str] = []

    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for filepath in scan_dir.rglob("*"):
            if filepath.suffix in SCAN_EXTENSIONS and filepath.is_file():
                all_issues.extend(scan_file(filepath))

    if all_issues:
        print("❌ Valores nutricionales fuera de rangos razonables:")
        print("\n".join(all_issues))
        print("\nRevisa que no haya bugs en el parsing o datos de test incorrectos.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
