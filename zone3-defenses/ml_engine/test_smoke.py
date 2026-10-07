"""In-process checks for /health and /score on benign request features."""

from __future__ import annotations

from fastapi.testclient import TestClient

from anomaly_detector import AnomalyDetector
from app import app, load_config

BENIGN = {
    "method": "GET",
    "path": "/api/status",
    "status_code": 200,
    "body_bytes": 400,
    "source_ip": "10.8.0.21",
    "user_agent": "Mozilla/5.0 (compatible; CyberForgeHealth/1.0)",
    "query": "view=summary",
    "timestamp": "2026-10-07T15:00:00Z",
}


def test_health_and_benign_score() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        body = health.json()
        assert body["status"] == "ok"
        assert body["model_ready"] is True
        assert body["model"] == "isolation_forest"

        scored = client.post("/score", json=BENIGN)
        assert scored.status_code == 200
        payload = scored.json()
        assert payload["model"] == "isolation_forest"
        assert 0.0 <= payload["anomaly_score"] <= 1.0
        assert payload["is_anomalous"] is False
        assert payload["features"]["method_code"] == 0.0
        assert payload["features"]["status_class"] == 2.0


def test_high_rate_is_outside_baseline() -> None:
    config = load_config()
    detector = AnomalyDetector(config)
    event = {
        "method": "GET",
        "path": "/api/status",
        "status_code": 200,
        "body_bytes": 400,
        "user_agent": "Mozilla/5.0 (compatible; CyberForgeHealth/1.0)",
        "query": "",
        "timestamp": "2026-10-07T15:00:00Z",
    }
    result = detector.score(event, request_rate=400)
    assert result.rate_zscore >= config["rate"]["zscore_threshold"]
    assert result.is_anomalous is True


def test_score_rejects_bad_status() -> None:
    with TestClient(app) as client:
        response = client.post("/score", json={"status_code": 99, "source_ip": "10.0.0.4"})
        assert response.status_code == 422
