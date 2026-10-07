# Security review — defensive core

This file records how to run the Phase 1 stack without turning the lab into an exposed, unauthenticated data store. It is operator guidance, not a formal audit.

## Scope of the running system

`docker-compose.yml` starts Elasticsearch, Kibana, Filebeat, a benign log generator, and the Zone 3 anomaly engine. It does not start target applications. Placeholder zone folders are empty on purpose.

Do not deploy intentionally vulnerable training applications to production, and do not add them to this compose file. Nothing in this phase is a substitute for production detection engineering.

## Network exposure

Host ports for Elasticsearch (`9200`), Kibana (`5601`), and the anomaly engine (`8088`) bind to `127.0.0.1` only. Containers talk to each other on the `cyberforge-defenses` bridge.

Elasticsearch runs with `xpack.security.enabled=false` so the local lab can boot without enrollment tokens. That setting is acceptable only while every listener stays on loopback. Before any shared or routed network:

- enable Elasticsearch security and TLS
- give Filebeat and Kibana their own credentials
- replace `KIBANA_ENCRYPTION_KEY` (the value in `.env.example` is a public placeholder)
- stop publishing the Elasticsearch port to developer workstations that are not the operator's own

The compose file does not mount the Docker socket. Filebeat reads a dedicated log volume, not the daemon API.

## Credentials

`.env.example` contains placeholders, including an unused `POSTGRES_PASSWORD`. Postgres is not started. Treat every value in that file as public. There is no production secret in the repository.

## Anomaly engine

`POST /score` accepts short request metadata and returns a numeric score against a synthetic benign baseline. Callers on the host can reach it through the published loopback port. The service:

- caps method, path, query, user-agent, and address fields
- does not fetch URLs, execute commands, or store raw bodies
- keeps a rolling per-source counter in memory and a fitted model under `/tmp` inside the container

Scores are advisory. A low score is not an allow decision, and a high score is not an incident classification. The baseline will not match a real application until an operator fits it on their own ordinary traffic.

Filebeat is started with `--strict.perms=false` because the config file is a read-only bind mount. Keep that file owned by the operator and mounted `:ro`.

## Log generator

The generator writes synthetic access lines for paths such as `/health` and `/api/status`. It is a telemetry fixture. It is not a traffic cannon and it does not generate exploit traffic. The entrypoint starts as root only long enough to create the log directory, then drops to the unprivileged `cyberforge` user.

## Images

Elastic images are pinned to `ELASTIC_VERSION` (default `8.19.23`). The Python services use `python:3.12-slim` and pinned requirements. Rebuild with `make up` after dependency changes.

## Reporting issues

If a defensive-core default exposes data beyond loopback, treat that as a bug in this stack. Offensive-zone placeholders are not a supported attack surface; leave them empty.
