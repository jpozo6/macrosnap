#!/usr/bin/env python3
"""Verifica que no se commiteen archivos .env y que .env.example esté actualizado."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True,
    )
    staged_files = result.stdout.strip().split("\n")

    errors: list[str] = []

    # 1. Verificar que no se commiteen archivos .env
    env_files = [f for f in staged_files if f.endswith(".env") or "/.env" in f]
    for env_file in env_files:
        if ".env.example" not in env_file and ".env.template" not in env_file:
            errors.append(f"  ⚠ Archivo .env en staging: {env_file} — NUNCA commitear archivos .env")

    # 2. Si hay cambios en config.py, verificar que .env.example tenga las mismas variables
    config_files = [f for f in staged_files if "config.py" in f]
    if config_files:
        env_example = Path("backend/.env.example")
        if env_example.exists():
            config_content = Path("backend/app/config.py").read_text(encoding="utf-8")
            example_content = env_example.read_text(encoding="utf-8")

            # Extraer variables de config.py (campos de Settings)
            import re
            config_vars = set(re.findall(r'(\w+):\s*str\s*=', config_content))
            example_vars = set(re.findall(r'^(\w+)=', example_content, re.MULTILINE))

            # Convertir a uppercase para comparar
            config_upper = {v.upper() for v in config_vars}
            missing = config_upper - example_vars
            if missing:
                errors.append(
                    f"  ⚠ Variables en config.py que faltan en .env.example: {missing}"
                )

    if errors:
        print("❌ Problemas con archivos de entorno:")
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
