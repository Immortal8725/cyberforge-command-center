# Kibana assets

Phase 1 ships one index pattern for the defensive access logs: `cyberforge-access-*`.

Per-level dashboard files under `dashboards/` are empty placeholders. They are not imported.

## Import

Start the stack (`make up`), then:

```bash
./kibana/import.sh
```

`KIBANA_URL` defaults to `http://127.0.0.1:5601`. The script posts `dashboards/00-index-patterns.ndjson` to Kibana's saved-object import API. Elasticsearch security is disabled in the local lab, so the request sends only the `kbn-xsrf` header.
