#!/usr/bin/env python3
"""Verifica que el tracing de LangSmith esté correctamente configurado."""

import re
import sys
from pathlib import Path

LANGSMITH_FILE = Path("backend/app/services/langsmith.py")
CONFIG_FILE = Path("backend/app/config.py")
MAIN_FILE = Path("backend/app/main.py")


def main() -> int:
    errors: list[str] = []

    # 1. Verificar que langsmith.py existe y configura LANGCHAIN_TRACING_V2
    if not LANGSMITH_FILE.exists():
        errors.append("  ⚠ No se encontró backend/app/services/langsmith.py")
    else:
        content = LANGSMITH_FILE.read_text(encoding="utf-8")
        if "LANGCHAIN_TRACING_V2" not in content:
            errors.append("  ⚠ langsmith.py no configura LANGCHAIN_TRACING_V2")
        if "LANGCHAIN_PROJECT" not in content:
            errors.append("  ⚠ langsmith.py no configura LANGCHAIN_PROJECT")
        if "LANGCHAIN_API_KEY" not in content:
            errors.append("  ⚠ langsmith.py no configura LANGCHAIN_API_KEY")

    # 2. Verificar que config.py tiene los campos de LangSmith
    if CONFIG_FILE.exists():
        config_content = CONFIG_FILE.read_text(encoding="utf-8")
        if "langsmith_api_key" not in config_content:
            errors.append("  ⚠ config.py no define langsmith_api_key")
        if "langsmith_project" not in config_content:
            errors.append("  ⚠ config.py no define langsmith_project")

    # 3. Verificar que setup_langsmith se llama en el arranque
    if MAIN_FILE.exists():
        main_content = MAIN_FILE.read_text(encoding="utf-8")
        if "setup_langsmith" not in main_content:
            errors.append("  ⚠ main.py no invoca setup_langsmith() — el tracing no se activará")

    # 4. Verificar que los nodos del grafo tienen metadata para tracing
    nodes_file = Path("backend/app/chain/nodes.py")
    if nodes_file.exists():
        nodes_content = nodes_file.read_text(encoding="utf-8")
        # Verificar que las funciones de nodos tienen docstrings (usados como run names)
        node_funcs = re.findall(r'def (\w+)\(state:', nodes_content)
        for func in node_funcs:
            pattern = rf'def {func}\(.*?\).*?:\s*\n\s*"""'
            if not re.search(pattern, nodes_content, re.DOTALL):
                errors.append(f"  ⚠ Nodo '{func}' sin docstring — afecta la identificación en LangSmith")

    if errors:
        print("❌ Problemas en la configuración de trazabilidad LangSmith:")
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
