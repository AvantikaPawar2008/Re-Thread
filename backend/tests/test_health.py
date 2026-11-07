"""Tests for /health endpoint."""


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "RE-THREAD"
    assert data["database"] == "connected"
    assert "version" in data


def test_health_models(client):
    """Test GET /health/models returns component statuses and active perception."""
    response = client.get("/health/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "active_perception" in data
    assert data["active_perception"] in ("local", "vlm", "stub")
    assert "perception_priority" in data
    assert "vlm_provider" in data
    assert "damage_yolo" in data["models"]
    assert "condition_resnet" in data["models"]
    assert "material_resnet" in data["models"]
    assert "vlm" in data["models"]
