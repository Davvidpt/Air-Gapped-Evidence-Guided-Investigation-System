#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$TASK_ROOT"
export PYTHONPATH="$TASK_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$TASK_ROOT/.venv/bin/python" -m streamlit run src/aegis/ui/dashboard.py \
  --server.address 127.0.0.1 --server.port 8501 --server.headless true \
  --server.maxUploadSize 100 --browser.gatherUsageStats false
