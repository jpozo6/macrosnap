"""Grafo LangGraph para el pipeline de análisis de macronutrientes."""

from langgraph.graph import END, StateGraph

from app.chain.nodes import calculate_macros, estimate_portions, identify_foods
from app.chain.state import AnalysisState


def _should_continue(state: AnalysisState) -> str:
    """Decide si continuar al siguiente nodo o terminar por error."""
    if state.get("error"):
        return "end"
    return "continue"


def build_analysis_graph() -> StateGraph:
    """Construye y compila el grafo de análisis de macronutrientes."""
    graph = StateGraph(AnalysisState)

    graph.add_node("identify_food", identify_foods)
    graph.add_node("estimate_portions", estimate_portions)
    graph.add_node("calculate_macros", calculate_macros)

    graph.set_entry_point("identify_food")

    graph.add_conditional_edges(
        "identify_food",
        _should_continue,
        {"continue": "estimate_portions", "end": END},
    )
    graph.add_conditional_edges(
        "estimate_portions",
        _should_continue,
        {"continue": "calculate_macros", "end": END},
    )
    graph.add_edge("calculate_macros", END)

    return graph.compile()


analysis_graph = build_analysis_graph()
