#!/usr/bin/env python3
"""Exporta el grafo de LangGraph como imagen Mermaid PNG y texto."""

import sys
import os

# Asegurar que el backend está en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.chain.graph import analysis_graph


def export_mermaid_text() -> str:
    """Exporta el grafo como texto Mermaid."""
    return analysis_graph.get_graph().draw_mermaid()


def export_png(output_path: str) -> None:
    """Exporta el grafo como imagen PNG."""
    try:
        png_data = analysis_graph.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(png_data)
        print(f"✅ Grafo exportado a {output_path}")
    except Exception as e:
        # Si no se puede generar PNG (falta dependencia), exportar solo texto
        print(f"⚠️  No se pudo generar PNG ({e}). Exportando Mermaid texto...")
        mermaid = export_mermaid_text()
        txt_path = output_path.replace(".png", ".mmd")
        with open(txt_path, "w") as f:
            f.write(mermaid)
        print(f"✅ Grafo Mermaid exportado a {txt_path}")


if __name__ == "__main__":
    output = os.path.join(
        os.path.dirname(__file__), "..", "docs", "graph.png"
    )
    os.makedirs(os.path.dirname(output), exist_ok=True)
    export_png(output)
    print("\nEstructura del grafo (Mermaid):")
    print(export_mermaid_text())
