# CyberForge Command Center

CyberForge is an enterprise cyber training range. This repository currently ships the **defensive core** only: local telemetry collection and a small anomaly-scoring service for ordinary HTTP access metadata.

The stack is meant to run on a single workstation or a private lab network. It is not a production SOC deployment, and it does not include training-target applications.

## What this change includes

- Elasticsearch, Kibana, and Filebeat
- A log generator that writes benign structured JSON access logs
- Zone 3 anomaly engine (`GET /health`, `POST /score`) using an Isolation Forest and a request-rate z-score
- Makefile targets, a runbook, and a health script for those services

## What is out of scope

Placeholder folders for other zones stay empty. This change does not add:

- intentionally vulnerable applications
- CTF challenges, flags, or exploit walkthroughs
- red-team scanners, fuzzers, or payload generators
- identity attack labs, WAF-bypass labs, supply-chain poison packages, or binary crackmes

Do not point this compose file at production traffic, and do not deploy vulnerable labs beside it. See [SECURITY-REVIEW.md](SECURITY-REVIEW.md).

## Prerequisites

- Docker Engine 24+ with Docker Compose v2
- About 2 GB of free RAM for Elasticsearch
- On Linux, Elasticsearch needs a higher virtual-memory map count:

```bash
sudo sysctl -w vm.max_map_count=262144
```

To keep that setting across reboots, write `vm.max_map_count=262144` to `/etc/sysctl.d/99-cyberforge.conf`.

## Bring up the defensive core

```bash
cp .env.example .env
make up
make ps
make health
```

`make health` checks Elasticsearch cluster health, the Kibana status API, and the anomaly engine `/health` and `/score` endpoints with a normal access-log sample.

Published ports bind to `127.0.0.1`:

| Service | URL |
| --- | --- |
| Elasticsearch | http://127.0.0.1:9200 |
| Kibana | http://127.0.0.1:5601 |
| Anomaly engine | http://127.0.0.1:8088 |

Filebeat reads `/var/log/cyberforge/access.jsonl` from a private volume and indexes documents into `cyberforge-access-*`. After Kibana is healthy, load the index pattern:

```bash
./kibana/import.sh
```

Score one benign request by hand:

```bash
curl -sS -X POST http://127.0.0.1:8088/score \
  -H 'content-type: application/json' \
  -d '{"method":"GET","path":"/health","status_code":200,"body_bytes":128,"source_ip":"10.0.0.8","user_agent":"CyberForgeHealth/1.0"}'
```

A typical response has `"model": "isolation_forest"`, an `anomaly_score` between 0 and 1, and `"is_anomalous": false` for this kind of sample. The score compares the request with a synthetic baseline of ordinary web traffic. It does not label attack types.

## Day-2 commands

```bash
make logs    # follow service logs
make ps      # container status
make down    # stop the stack and keep volumes
make config  # render docker compose config
```

`make down` keeps the Elasticsearch data volume and the log volume. Remove them with `docker compose down -v` when you want a clean disk.

Postgres variables in `.env.example` are reserved for a later phase. This compose file does not start a database.

## Tests without Docker

The anomaly engine can be checked in-process:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r zone3-defenses/ml_engine/requirements.txt \
            -r zone3-defenses/ml_engine/requirements-dev.txt
make test
```

`tests/verify-defensive-core.sh` is the live check used by `make health`. Level scripts under `tests/levels/` are unused placeholders.

## Layout

```text
docker-compose.yml          defensive core services
zone3-defenses/filebeat.yml Filebeat input and Elasticsearch output
zone3-defenses/log_generator/  benign JSON access logs
zone3-defenses/ml_engine/   anomaly scoring API
kibana/                     index-pattern import
tests/verify-defensive-core.sh
```

Further reading: [ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md), [RUNBOOK.md](RUNBOOK.md), [SECURITY-REVIEW.md](SECURITY-REVIEW.md).
