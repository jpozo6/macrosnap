"""Tests para los servicios de la aplicación."""

import os
from unittest.mock import patch

import pytest

from app.services.llm import get_llm


class TestGetLlm:
    """Tests para la función get_llm."""

    @patch("app.services.llm.settings")
    def test_sin_api_key_falla(self, mock_settings: object) -> None:
        mock_settings.google_api_key = ""
        with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
            get_llm()

    @patch("app.services.llm.settings")
    def test_con_api_key_retorna_llm(self, mock_settings: object) -> None:
        mock_settings.google_api_key = "fake-key-for-test"
        llm = get_llm()
        assert llm is not None
        assert "gemini-3-flash-preview" in llm.model


class TestSetupLangsmith:
    """Tests para setup_langsmith."""

    @patch("app.services.langsmith.settings")
    def test_con_api_key_activa_tracing(self, mock_settings: object) -> None:
        mock_settings.langsmith_api_key = "lsv2_test_key"
        mock_settings.langsmith_project = "test-project"

        from app.services.langsmith import setup_langsmith
        setup_langsmith()

        assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
        assert os.environ.get("LANGCHAIN_PROJECT") == "test-project"

    @patch("app.services.langsmith.settings")
    def test_sin_api_key_desactiva_tracing(self, mock_settings: object) -> None:
        mock_settings.langsmith_api_key = ""

        from app.services.langsmith import setup_langsmith
        setup_langsmith()

        assert os.environ.get("LANGCHAIN_TRACING_V2") == "false"
