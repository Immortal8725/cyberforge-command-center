"""Live smoke check for GET /health and POST /score on a benign sample.

Usage:
    ML_ENGINE_URL=http://127.0.0.1:8088 python smoke.py
"""

from __future__ import annotations

import json
import os
import sys

import requests

BENIGN_SAMPLE = {
    "method": "GET",
    "path": "/health",
    "status_code": 200,
    "body_bytes": 128,
    "source_ip": "10.0.0.8",
    "user_agent": "CyberForgeHealth/1.0",
    "query": "",
    "timestamp": "2026-10-07T15:00:00Z",
}


def check(base_url: str) -> dict:
    """Return health and score payloads. Raise if the benign sample is flagged."""
    root = base_url.rstrip("/")
    health = requests.get(f"{root}/health", timeout=5)
    health.raise_for_status()
    health_body = health.json()
    if health_body.get("status") != "ok" or not health_body.get("model_ready"):
        raise RuntimeError(f"anomaly engine is not ready: {health_body}")

    scored = requests.post(f"{root}/score", json=BENIGN_SAMPLE, timeout=5)
    scored.raise_for_status()
    score_body = scored.json()
    if score_body.get("is_anomalous"):
        raise RuntimeError(f"benign sample was flagged: {score_body}")
    if not 0.0 <= float(score_body["anomaly_score"]) <= 1.0:
        raise RuntimeError(f"anomaly_score out of range: {score_body}")
    return {"health": health_body, "score": score_body}


def main() -> int:
    base_url = os.environ.get("ML_ENGINE_URL", "http://127.0.0.1:8080")
    try:
        report = check(base_url)
    except (requests.RequestException, RuntimeError, KeyError, ValueError) as exc:
        print(f"smoke failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
