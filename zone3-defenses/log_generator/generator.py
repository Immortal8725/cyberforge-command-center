"""Write benign structured HTTP access logs as JSON lines.

The generator is a telemetry fixture for Filebeat. Paths, methods, and status
codes stay inside ordinary web traffic. It does not craft exploit requests.
"""

from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(os.environ.get("CYBERFORGE_LOG_PATH", "/var/log/cyberforge/access.jsonl"))
MAX_BYTES = 5 * 1024 * 1024

PATHS = (
    "/",
    "/health",
    "/ready",
    "/api/status",
    "/api/catalog",
    "/dashboard",
    "/docs",
    "/static/app.css",
    "/static/app.js",
    "/account/profile",
)
METHODS = ("GET", "GET", "GET", "GET", "POST", "HEAD")
STATUSES = (200, 200, 200, 200, 204, 301, 304, 404)
AGENTS = (
    "Mozilla/5.0 (compatible; CyberForgeHealth/1.0)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128.0.0.0",
    "CyberForgeMonitor/1.0",
)


def _event(rng: random.Random) -> dict:
    method = rng.choice(METHODS)
    status = rng.choice(STATUSES)
    body = 0 if method == "HEAD" else rng.randint(80, 2400)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return {
        "@timestamp": now,
        "http": {
            "request": {"method": method},
            "response": {"status_code": status, "body": {"bytes": body}},
        },
        "url": {"path": rng.choice(PATHS)},
        "source": {"ip": f"10.0.0.{rng.randint(2, 40)}"},
        "user_agent": {"original": rng.choice(AGENTS)},
    }


def _append(line: str) -> None:
    if LOG_PATH.exists() and LOG_PATH.stat().st_size > MAX_BYTES:
        LOG_PATH.write_text("", encoding="utf-8")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main() -> None:
    rng = random.Random()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    while True:
        _append(json.dumps(_event(rng), separators=(",", ":")))
        time.sleep(rng.uniform(0.8, 2.0))


if __name__ == "__main__":
    main()
