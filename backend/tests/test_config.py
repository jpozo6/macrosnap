"""Tests para la configuración de la aplicación."""

from app.config import Settings


class TestSettings:
    """Tests para la clase Settings."""

    def test_default_values(self) -> None:
        settings = Settings(
            google_api_key="",
            langsmith_api_key="",
            _env_file=None,
        )
        assert settings.google_api_key == ""
        assert settings.langsmith_project == "macrosnap"
        assert "sqlite" in settings.database_url

    def test_custom_values(self) -> None:
        settings = Settings(
            google_api_key="test-key",
            langsmith_api_key="ls-test",
            langsmith_project="test-project",
            database_url="sqlite:///test.db",
            _env_file=None,
        )
        assert settings.google_api_key == "test-key"
        assert settings.langsmith_api_key == "ls-test"
        assert settings.langsmith_project == "test-project"
        assert settings.database_url == "sqlite:///test.db"
