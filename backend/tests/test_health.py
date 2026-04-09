"""Tests para el endpoint de health check."""

from fastapi.testclient import TestClient


class TestHealthCheck:
    """Tests para GET /health."""

    def test_health_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
