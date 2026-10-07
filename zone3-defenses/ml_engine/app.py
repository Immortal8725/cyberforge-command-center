"""HTTP API for the Zone 3 anomaly engine."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from anomaly_detector import AnomalyDetector
from baseline_store import BaselineStore

logger = logging.getLogger("cyberforge.ml_engine")

_MAX_PATH = 2048
_MAX_QUERY = 1024
_MAX_AGENT = 512
_MAX_IP = 64


def load_config() -> dict:
    """Load config.yaml and apply environment overrides."""
    path = Path(__file__).with_name("config.yaml")
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if threshold := os.environ.get("ML_SCORE_THRESHOLD"):
        config["model"]["score_threshold"] = float(threshold)
    if z_threshold := os.environ.get("ML_RATE_ZSCORE_THRESHOLD"):
        config["rate"]["zscore_threshold"] = float(z_threshold)
    if baseline_path := os.environ.get("ML_BASELINE_PATH"):
        config["baseline"]["path"] = baseline_path
    return config


class ScoreRequest(BaseModel):
    method: str = "GET"
    path: str = "/"
    status_code: int = 200
    body_bytes: int = 0
    source_ip: str = "0.0.0.0"
    user_agent: str = ""
    query: str = ""
    timestamp: str | None = None

    @field_validator("method")
    @classmethod
    def method_token(cls, value: str) -> str:
        token = value.strip().upper()
        if not token.isascii() or not token.isalnum() or len(token) > 16:
            raise ValueError("method must be a short HTTP method token")
        return token

    @field_validator("path")
    @classmethod
    def path_bound(cls, value: str) -> str:
        if len(value) > _MAX_PATH:
            raise ValueError("path is too long")
        return value

    @field_validator("query")
    @classmethod
    def query_bound(cls, value: str) -> str:
        if len(value) > _MAX_QUERY:
            raise ValueError("query is too long")
        return value

    @field_validator("user_agent")
    @classmethod
    def agent_bound(cls, value: str) -> str:
        if len(value) > _MAX_AGENT:
            raise ValueError("user_agent is too long")
        return value

    @field_validator("source_ip")
    @classmethod
    def ip_bound(cls, value: str) -> str:
        text = value.strip()
        if not text or len(text) > _MAX_IP:
            raise ValueError("source_ip must be a short address label")
        return text

    @field_validator("status_code")
    @classmethod
    def status_range(cls, value: int) -> int:
        if value < 100 or value > 599:
            raise ValueError("status_code must be an HTTP status")
        return value

    @field_validator("body_bytes")
    @classmethod
    def body_non_negative(cls, value: int) -> int:
        if value < 0 or value > 50_000_000:
            raise ValueError("body_bytes is out of range")
        return value


class ScoreResponse(BaseModel):
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    rate_zscore: float
    is_anomalous: bool
    model: str
    features: dict[str, float]


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    store = BaselineStore(
        window_seconds=float(config["rate"]["window_seconds"]),
        path=str(config["baseline"]["path"]),
    )
    detector = AnomalyDetector(config)
    try:
        store.save(detector.bundle())
    except OSError:
        logger.warning("baseline bundle was not persisted", exc_info=True)
    app.state.config = config
    app.state.store = store
    app.state.detector = detector
    logger.info(
        "model ready algorithm=%s rate_mean=%.2f",
        detector.algorithm,
        detector.rate_mean,
    )
    yield


app = FastAPI(title="CyberForge Anomaly Engine", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    detector = getattr(app.state, "detector", None)
    ready = detector is not None
    return {
        "status": "ok" if ready else "starting",
        "model_ready": ready,
        "model": detector.algorithm if ready else None,
    }


@app.post("/score", response_model=ScoreResponse)
def score(body: ScoreRequest) -> ScoreResponse:
    detector: AnomalyDetector | None = getattr(app.state, "detector", None)
    store: BaselineStore | None = getattr(app.state, "store", None)
    if detector is None or store is None:
        raise HTTPException(status_code=503, detail="model is not ready")
    request_rate = store.observe(body.source_ip)
    result = detector.score(body.model_dump(), request_rate)
    return ScoreResponse(
        anomaly_score=result.anomaly_score,
        rate_zscore=result.rate_zscore,
        is_anomalous=result.is_anomalous,
        model=detector.algorithm,
        features=result.features,
    )
