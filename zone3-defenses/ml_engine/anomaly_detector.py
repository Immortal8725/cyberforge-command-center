"""Isolation Forest scorer trained on a synthetic benign HTTP baseline.

The model measures distance from ordinary request shape and rate. It does not
name or detect attack techniques.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from feature_extractor import FEATURE_NAMES, extract


@dataclass(frozen=True)
class ScoreResult:
    anomaly_score: float
    rate_zscore: float
    is_anomalous: bool
    features: dict[str, float]


class AnomalyDetector:
    """Fit once on synthetic normal traffic, then score new observations."""

    def __init__(self, config: dict) -> None:
        model_cfg = config["model"]
        rate_cfg = config["rate"]
        self.algorithm = str(model_cfg.get("algorithm", "isolation_forest"))
        self.score_threshold = float(model_cfg["score_threshold"])
        self.zscore_threshold = float(rate_cfg["zscore_threshold"])
        self._forest = IsolationForest(
            n_estimators=int(model_cfg["n_estimators"]),
            contamination=float(model_cfg["contamination"]),
            random_state=int(model_cfg["random_state"]),
            n_jobs=1,
        )
        frame = _synthetic_frame(
            int(model_cfg["baseline_samples"]),
            int(model_cfg["random_state"]),
        )
        self._forest.fit(frame.to_numpy())
        self.rate_mean = float(frame["request_rate"].mean())
        self.rate_std = float(frame["request_rate"].std(ddof=1)) or 1.0

    def score(self, event: dict, request_rate: float) -> ScoreResult:
        features = extract(event, request_rate)
        decision = float(self._forest.decision_function([features])[0])
        anomaly_score = _to_unit_interval(decision)
        rate_zscore = (float(request_rate) - self.rate_mean) / self.rate_std
        flagged = anomaly_score >= self.score_threshold or rate_zscore >= self.zscore_threshold
        named = {name: float(value) for name, value in zip(FEATURE_NAMES, features, strict=True)}
        return ScoreResult(
            anomaly_score=round(anomaly_score, 6),
            rate_zscore=round(rate_zscore, 6),
            is_anomalous=bool(flagged),
            features=named,
        )

    def bundle(self) -> dict:
        """Serializable warmup state. The live forest is refit on startup."""
        return {
            "algorithm": self.algorithm,
            "rate_mean": self.rate_mean,
            "rate_std": self.rate_std,
            "score_threshold": self.score_threshold,
            "zscore_threshold": self.zscore_threshold,
        }


def _to_unit_interval(decision: float) -> float:
    """Map Isolation Forest's decision_function onto an anomaly score in (0, 1).

    Higher decision values are more consistent with the baseline. The returned
    score is higher when the point is less consistent with that baseline.
    """
    return 1.0 / (1.0 + math.exp(decision * 10.0))


def _synthetic_frame(samples: int, seed: int) -> pd.DataFrame:
    """Ordinary web traffic: short paths, common methods, modest sizes, low rates."""
    rng = np.random.default_rng(seed)
    method = rng.choice([0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 2.0], size=samples)
    status_class = rng.choice([2.0, 2.0, 2.0, 2.0, 3.0, 4.0], size=samples)
    path_length = rng.integers(1, 32, size=samples).astype(float)
    query_length = rng.integers(0, 16, size=samples).astype(float)
    body_bytes = rng.integers(0, 2500, size=samples).astype(float)
    ua_length = rng.integers(20, 110, size=samples).astype(float)
    hour = rng.integers(8, 19, size=samples).astype(float)
    request_rate = rng.integers(1, 10, size=samples).astype(float)
    frame = pd.DataFrame(
        {
            "method_code": method,
            "status_class": status_class,
            "path_length": path_length,
            "query_length": query_length,
            "body_bytes": body_bytes,
            "ua_length": ua_length,
            "hour": hour,
            "request_rate": request_rate,
        }
    )
    return frame.loc[:, list(FEATURE_NAMES)]
