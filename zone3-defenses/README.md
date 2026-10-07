# Zone 3 — defenses

This zone is the Phase 1 defensive core.

- `filebeat.yml` reads benign JSON access logs and writes them to Elasticsearch.
- `log_generator/` emits those logs. It is not an attack simulator.
- `ml_engine/` scores request metadata with an Isolation Forest and a rate z-score.

Bring the services up from the repository root with `make up`. See the root `README.md`.
