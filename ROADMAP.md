# Roadmap

## Phase 1 — Defensive core (this change)

- Single-node Elasticsearch and Kibana for local search
- Filebeat shipping benign structured access logs
- Zone 3 anomaly engine with `/health` and `/score`
- Health script and operator docs for that stack

Phase 1 is complete when `docker compose config` renders, `make up` starts the five services, and `make health` passes.

## Phase 2 — Defensive operations

Possible follow-on work, still limited to detection and operations:

- Persist anomaly scores next to the access index
- Kibana views for request volume and score trends
- Authenticated Elasticsearch and TLS for any non-local deployment
- A real baseline built from the operator's own benign logs, replacing the synthetic warmup model

## Explicitly not in this roadmap

Target applications, challenge platforms, flags, and offensive labs are not milestones of this repository phase. Those ideas, including anything under Zone 2, stay external and are not specified here. Placeholder directories remain empty so later work cannot be confused with the defensive core.
