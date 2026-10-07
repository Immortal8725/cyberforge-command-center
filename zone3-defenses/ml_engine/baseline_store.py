"""Rolling per-source request counts and joblib persistence for the warmup model."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from pathlib import Path

import joblib


class BaselineStore:
    """Count requests inside a sliding window and optionally persist a model bundle."""

    def __init__(self, window_seconds: float, path: str | None = None) -> None:
        self.window_seconds = float(window_seconds)
        self.path = Path(path) if path else None
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def observe(self, source_ip: str, now: float | None = None) -> float:
        """Record one request and return how many fell inside the window."""
        moment = time.time() if now is None else now
        with self._lock:
            bucket = self._events[source_ip]
            bucket.append(moment)
            cutoff = moment - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            return float(len(bucket))

    def save(self, payload: dict) -> None:
        """Persist a model bundle. Missing parent directories are created."""
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(payload, self.path)

    def load(self) -> dict | None:
        """Return a previously saved bundle, or None when no file exists."""
        if self.path is None or not self.path.exists():
            return None
        loaded = joblib.load(self.path)
        if not isinstance(loaded, dict):
            return None
        return loaded
