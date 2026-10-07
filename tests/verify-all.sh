#!/usr/bin/env bash
# Phase 1 runs defensive-core readiness checks only.
set -euo pipefail
echo "Level verification is out of scope for this PR — defensive core only."
exec "$(cd "$(dirname "$0")" && pwd)/verify-defensive-core.sh"
