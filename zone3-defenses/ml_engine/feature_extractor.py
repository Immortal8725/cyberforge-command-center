"""Numeric features for ordinary HTTP request metadata.

The vector describes shape and rate. It does not inspect message bodies for
signatures and it is not an attack classifier.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

FEATURE_NAMES = (
    "method_code",
    "status_class",
    "path_length",
    "query_length",
    "body_bytes",
    "ua_length",
    "hour",
    "request_rate",
)

_METHODS = {
    "GET": 0.0,
    "HEAD": 1.0,
    "POST": 2.0,
    "PUT": 3.0,
    "DELETE": 4.0,
    "PATCH": 5.0,
    "OPTIONS": 6.0,
}


def extract(event: Mapping, request_rate: float) -> list[float]:
    """Return one feature row aligned with FEATURE_NAMES."""
    method = str(event.get("method", "GET")).upper()
    path = str(event.get("path", "/"))
    query = str(event.get("query") or "")
    user_agent = str(event.get("user_agent") or "")
    status = int(event.get("status_code", 200))
    body_bytes = float(event.get("body_bytes") or 0)
    status_class = float(min(5, max(1, status // 100)))
    return [
        _METHODS.get(method, 7.0),
        status_class,
        float(len(path)),
        float(len(query)),
        body_bytes,
        float(len(user_agent)),
        _hour(event.get("timestamp")),
        float(request_rate),
    ]


def _hour(value: object) -> float:
    if value is None or value == "":
        return float(datetime.now(timezone.utc).hour)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return float(datetime.now(timezone.utc).hour)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return float(parsed.astimezone(timezone.utc).hour)
