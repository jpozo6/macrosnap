#!/usr/bin/env python3
"""Valida que cambios en models.py tengan migraciones correspondientes."""

import subprocess
import sys
from pathlib import Path

MODELS_FILE = "backend/app/models.py"
MIGRATIONS_DIR = Path("backend/migrations") if Path("backend/migrations").exists() else Path("backend/alembic")


def main() -> int:
    # Verificar si models.py tiene cambios staged
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True,
    )
    staged_files = result.stdout.strip().split("\n")

    if MODELS_FILE not in staged_files:
        return 0  # No hay cambios en models, nada que verificar

    # Verificar qué cambió en models.py
    diff_result = subprocess.run(
        ["git", "diff", "--cached", "--", MODELS_FILE],
        capture_output=True, text=True,
    )
    diff = diff_result.stdout

    # Detectar cambios estructurales (nuevas columnas, tablas, constraints)
    structural_changes = any(
        keyword in diff
        for keyword in ["Column(", "__tablename__", "ForeignKey", "Index(", "UniqueConstraint"]
    )

    if not structural_changes:
        return 0  # Solo cambios cosméticos/lógicos, no requiere migración

    # Verificar que hay archivos de migración staged
    migration_files = [f for f in staged_files if "migration" in f.lower() or "alembic" in f.lower()]

    if not migration_files:
        # Verificar si al menos existe el directorio de migraciones
        errors: list[str] = []
        if not MIGRATIONS_DIR.exists():
            errors.append(
                "  ⚠ Se detectaron cambios estructurales en models.py pero no existe "
                "directorio de migraciones (backend/migrations/ o backend/alembic/)"
            )
            errors.append("  💡 Considera configurar Alembic: alembic init backend/migrations")
        else:
            errors.append(
                "  ⚠ Se detectaron cambios estructurales en models.py "
                "pero no hay migraciones staged en el commit"
            )
            errors.append("  💡 Genera una migración: alembic revision --autogenerate -m 'descripción'")

        print("❌ Falta migración de base de datos:")
        print("\n".join(errors))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
