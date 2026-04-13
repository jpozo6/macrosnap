"""Tests para los scripts de validación de hooks."""

import subprocess
import sys
from pathlib import Path

VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / ".claude" / "hooks" / "validators"


def _run_validator(name: str) -> subprocess.CompletedProcess:
    """Ejecuta un validador y retorna el resultado."""
    script = VALIDATORS_DIR / name
    env = {**subprocess.os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent.parent),
        env=env,
    )


class TestCheckPrompts:
    """Tests para el validador de prompts."""

    def test_prompts_validos(self) -> None:
        result = _run_validator("check_prompts.py")
        assert result.returncode == 0


class TestCheckMacroSchema:
    """Tests para el validador de consistencia del schema."""

    def test_schema_consistente(self) -> None:
        result = _run_validator("check_macro_schema.py")
        assert result.returncode == 0, f"Schema inconsistente: {result.stdout}"


class TestCheckLanggraph:
    """Tests para el validador del grafo LangGraph."""

    def test_grafo_valido(self) -> None:
        result = _run_validator("check_langgraph.py")
        assert result.returncode == 0, f"Grafo inválido: {result.stdout}"


class TestCheckParseTests:
    """Tests para el validador de parsing."""

    def test_parse_tests_pasan(self) -> None:
        result = _run_validator("check_parse_tests.py")
        assert result.returncode == 0, f"Tests de parsing fallidos: {result.stdout}"


class TestCheckLangsmithTracing:
    """Tests para el validador de trazabilidad LangSmith."""

    def test_langsmith_configurado(self) -> None:
        result = _run_validator("check_langsmith_tracing.py")
        assert result.returncode == 0, f"LangSmith mal configurado: {result.stdout}"


class TestCheckCostEstimate:
    """Tests para el estimador de coste."""

    def test_coste_dentro_de_umbral(self) -> None:
        result = _run_validator("check_cost_estimate.py")
        assert result.returncode == 0
        assert "Coste estimado" in result.stdout
