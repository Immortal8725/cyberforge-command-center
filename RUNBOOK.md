# Runbook — defensive core

Operate only the services in `docker-compose.yml`. Commands assume the repository root and Docker Compose v2.

## Start

```bash
cp .env.example .env   # first run, or after pulling port changes
sudo sysctl -w vm.max_map_count=262144
make up
make ps
```

Wait until `elasticsearch` and `kibana` report healthy. Kibana often needs a minute after Elasticsearch goes yellow.

```bash
make health
./kibana/import.sh
```

## Stop

```bash
make down
```

Volumes `es-data` and `cyberforge-logs` remain. Delete them with:

```bash
docker compose down -v
```

## Logs and status

```bash
make logs
make ps
docker compose logs elasticsearch --tail=100
docker compose logs ml_engine --tail=100
```

## Health checks

`make health` calls `tests/verify-defensive-core.sh`, which requires:

1. `GET http://127.0.0.1:9200/_cluster/health` returns `green` or `yellow`
2. `GET http://127.0.0.1:5601/api/status` succeeds
3. `GET http://127.0.0.1:8088/health` returns `"status": "ok"`
4. `POST http://127.0.0.1:8088/score` accepts a normal access sample and returns an `anomaly_score`

Override URLs with `ELASTICSEARCH_URL`, `KIBANA_URL`, and `ML_ENGINE_URL` when ports in `.env` differ from the defaults.

In-process engine tests, with no Docker dependency:

```bash
pip install -r zone3-defenses/ml_engine/requirements.txt \
            -r zone3-defenses/ml_engine/requirements-dev.txt
make test
```

## Failures

**Elasticsearch exits during bootstrap checks.** The host `vm.max_map_count` is below 262144. Set it as shown above and run `make up` again.

**Elasticsearch is red on disk watermarks.** Free disk space. The node uses a 512 MB heap via `ES_JAVA_OPTS`.

**Kibana stays unhealthy.** Confirm Elasticsearch is yellow or green, then read `docker compose logs kibana`. The saved-object encryption key must be at least 32 characters (`KIBANA_ENCRYPTION_KEY`).

**Filebeat config health fails.** `zone3-defenses/filebeat.yml` is mounted read-only. Compose starts Filebeat with `--strict.perms=false` because bind-mounted configs are often group-writable on the host. Do not mount the Docker socket to debug Filebeat.

**`/score` marks ordinary traffic anomalous.** The model is a synthetic warmup baseline, not a profile of a real site. Treat scores as a lab signal. Recalibration belongs to a later phase.

**Port already in use.** Change `ELASTICSEARCH_PORT`, `KIBANA_PORT`, or `ML_ENGINE_PORT` in `.env`, then `make down && make up`.

## What this runbook does not cover

There is no procedure here for target applications, challenge imports, or other zone compose files. Those files are empty placeholders.
