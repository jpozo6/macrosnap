#!/usr/bin/env python3
"""Verifica type hints en archivos Python modificados."""

import ast
import subprocess
import sys
from pathlib import Path


def check_type_hints(filepath: str) -> list[str]:
    """Verifica que las funciones públicas tengan type hints."""
    issues: list[str] = []
    path = Path(filepath)
    if not path.exists() or path.suffix != ".py":
        return []

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return [f"  ⚠ {filepath}: error de sintaxis Python"]

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Ignorar funciones privadas y dunder
            if node.name.startswith("_"):
                continue
            # Verificar return type
            if node.returns is None:
                issues.append(
                    f"  ⚠ {filepath}:{node.lineno} — función '{node.name}' sin return type hint"
                )
            # Verificar parámetros (ignorar self/cls)
            for arg in node.args.args:
                if arg.arg in ("self", "cls"):
                    continue
                if arg.annotation is None:
                    issues.append(
                        f"  ⚠ {filepath}:{node.lineno} — parámetro '{arg.arg}' en '{node.name}' sin type hint"
                    )
    return issues


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True,
    )
    staged_files = [
        f for f in result.stdout.strip().split("\n")
        if f.endswith(".py") and f.startswith("backend/")
    ]

    all_issues: list[str] = []
    for filepath in staged_files:
        all_issues.extend(check_type_hints(filepath))

    if all_issues:
        print("❌ Faltan type hints (obligatorios por convención del proyecto):")
        print("\n".join(all_issues))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
