"""Tests para la estructura del grafo LangGraph."""

from app.chain.graph import analysis_graph, build_analysis_graph


class TestBuildAnalysisGraph:
    """Tests para la construcción del grafo."""

    def test_grafo_se_compila(self) -> None:
        graph = build_analysis_graph()
        assert graph is not None

    def test_grafo_singleton_existe(self) -> None:
        assert analysis_graph is not None

    def test_grafo_tiene_nodos_esperados(self) -> None:
        graph = build_analysis_graph()
        node_names = set(graph.get_graph().nodes.keys())
        assert "identify_food" in node_names
        assert "estimate_portions" in node_names
        assert "calculate_macros" in node_names

    def test_grafo_entry_point_es_identify_food(self) -> None:
        graph = build_analysis_graph()
        graph_repr = graph.get_graph()
        start_edges = [
            e.target for e in graph_repr.edges
            if e.source == "__start__"
        ]
        assert "identify_food" in start_edges
