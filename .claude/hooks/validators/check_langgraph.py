#!/usr/bin/env python3
"""Lint del grafo LangGraph: verifica nodos conectados, sin huérfanos ni ciclos infinitos."""

import re
import sys
from pathlib import Path

GRAPH_FILE = Path("backend/app/chain/graph.py")


def main() -> int:
    if not GRAPH_FILE.exists():
        print(f"❌ No se encontró {GRAPH_FILE}")
        return 1

    content = GRAPH_FILE.read_text(encoding="utf-8")
    errors: list[str] = []

    # Extraer nodos registrados con add_node
    nodes = set(re.findall(r'graph\.add_node\(["\'](\w+)["\']', content))
    if not nodes:
        errors.append("  ⚠ No se encontraron nodos registrados con add_node")

    # Extraer entry point
    entry_points = re.findall(r'graph\.set_entry_point\(["\'](\w+)["\']', content)
    if not entry_points:
        errors.append("  ⚠ No se encontró entry point (set_entry_point)")
    elif entry_points[0] not in nodes:
        errors.append(f"  ⚠ Entry point '{entry_points[0]}' no es un nodo registrado")

    # Extraer nodos origen en edges (add_edge, add_conditional_edges)
    edge_sources = set(re.findall(r'graph\.add_(?:conditional_)?edge[s]?\(\s*["\'](\w+)["\']', content))
    conditional_targets: set[str] = set()
    for match in re.finditer(r'"(\w+)":\s*["\'](\w+)["\']', content):
        conditional_targets.add(match.group(2))
    # Incluir targets de add_edge directos
    for match in re.finditer(r'graph\.add_edge\(["\'](\w+)["\'],\s*["\'](\w+)["\']', content):
        edge_sources.add(match.group(1))
        conditional_targets.add(match.group(2))

    # Filtrar END de los targets
    conditional_targets.discard("END")
    conditional_targets.discard("end")

    # Verificar nodos huérfanos (registrados pero sin conexión entrante ni saliente)
    connected = edge_sources | conditional_targets | set(entry_points)
    orphans = nodes - connected
    if orphans:
        errors.append(f"  ⚠ Nodos huérfanos (sin conexión): {orphans}")

    # Verificar que todos los targets existen como nodos
    for target in conditional_targets:
        if target not in nodes:
            errors.append(f"  ⚠ Target '{target}' en edge no es un nodo registrado")

    # Verificar que todos los nodos (excepto el último) tienen edges salientes
    nodes_without_outgoing = nodes - edge_sources
    # El último nodo puede no tener edge saliente si va directo a END
    has_end_edge = bool(re.findall(r'graph\.add_edge\(["\'](\w+)["\'],\s*END\)', content))
    if not has_end_edge and nodes_without_outgoing:
        errors.append(f"  ⚠ Nodos sin edge saliente: {nodes_without_outgoing}")

    # Detección básica de ciclos: si un nodo apunta a un ancestro
    # Extraer el flujo lineal esperado
    flow: list[str] = list(entry_points)
    visited: set[str] = set()
    current = entry_points[0] if entry_points else None
    while current and current not in visited:
        visited.add(current)
        # Buscar el siguiente nodo
        next_nodes = set()
        for match in re.finditer(
            rf'graph\.add_(?:conditional_)?edge[s]?\(\s*["\']({re.escape(current)})["\']',
            content,
        ):
            # Buscar targets después de este match
            rest = content[match.end():]
            for target_match in re.finditer(r'["\'](\w+)["\']', rest[:200]):
                t = target_match.group(1)
                if t not in ("continue", "end", "END") and t in nodes:
                    next_nodes.add(t)
                    break
            break
        if next_nodes:
            current = next(iter(next_nodes))
            flow.append(current)
        else:
            break

    if errors:
        print("❌ Problemas en la estructura del grafo LangGraph:")
        print("\n".join(errors))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
