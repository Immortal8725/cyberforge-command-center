#!/usr/bin/env bash
# Import the defensive-core access-log index pattern into local Kibana.
set -euo pipefail

KIBANA_URL="${KIBANA_URL:-http://127.0.0.1:5601}"
DIR="$(cd "$(dirname "$0")" && pwd)"
NDJSON="${DIR}/dashboards/00-index-patterns.ndjson"

if [[ ! -s "${NDJSON}" ]]; then
  echo "missing index pattern: ${NDJSON}" >&2
  exit 1
fi

echo "Waiting for Kibana at ${KIBANA_URL}/api/status"
ready=0
for _ in $(seq 1 60); do
  if curl -sf "${KIBANA_URL}/api/status" >/dev/null; then
    ready=1
    break
  fi
  sleep 2
done

if [[ "${ready}" -ne 1 ]]; then
  echo "Kibana did not become ready at ${KIBANA_URL}" >&2
  exit 1
fi

curl -fsS -X POST "${KIBANA_URL}/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" \
  --form "file=@${NDJSON}"
echo
echo "Imported ${NDJSON}"
