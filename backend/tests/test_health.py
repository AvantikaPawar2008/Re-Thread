"""Tests for /health endpoint."""


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "RE-THREAD"
    assert data["database"] == "connected"
    assert "version" in data
