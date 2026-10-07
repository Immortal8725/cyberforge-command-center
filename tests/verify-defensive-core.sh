#!/usr/bin/env bash
# Readiness checks for Elasticsearch, Kibana, and the anomaly engine.
# Uses a normal access-log sample only.
set -euo pipefail

ES_URL="${ELASTICSEARCH_URL:-http://127.0.0.1:${ELASTICSEARCH_PORT:-9200}}"
KIBANA_URL="${KIBANA_URL:-http://127.0.0.1:${KIBANA_PORT:-5601}}"
ML_URL="${ML_ENGINE_URL:-http://127.0.0.1:${ML_ENGINE_PORT:-8088}}"

echo "elasticsearch ${ES_URL}/_cluster/health"
health="$(curl -fsS "${ES_URL}/_cluster/health")"
echo "${health}"
python3 -c 'import json,sys; body=json.loads(sys.argv[1]); status=body.get("status");
raise SystemExit(0 if status in ("green","yellow") else f"unexpected status {status}")' "${health}"

echo "kibana ${KIBANA_URL}/api/status"
curl -fsS "${KIBANA_URL}/api/status" >/dev/null
echo "kibana ok"

echo "ml_engine ${ML_URL}/health"
ml_health="$(curl -fsS "${ML_URL}/health")"
echo "${ml_health}"
python3 -c 'import json,sys; body=json.loads(sys.argv[1]);
ok=body.get("status")=="ok" and body.get("model_ready") is True
raise SystemExit(0 if ok else f"engine not ready: {body}")' "${ml_health}"

echo "ml_engine ${ML_URL}/score"
score="$(curl -fsS -X POST "${ML_URL}/score" \
  -H "content-type: application/json" \
  -d '{"method":"GET","path":"/health","status_code":200,"body_bytes":128,"source_ip":"10.0.0.8","user_agent":"CyberForgeHealth/1.0","query":"","timestamp":"2026-10-07T15:00:00Z"}')"
echo "${score}"
python3 -c 'import json,sys; body=json.loads(sys.argv[1]);
score=float(body["anomaly_score"])
ok=0.0<=score<=1.0 and body.get("is_anomalous") is False and body.get("model")=="isolation_forest"
raise SystemExit(0 if ok else f"unexpected score payload: {body}")' "${score}"

echo "defensive core health checks passed"
