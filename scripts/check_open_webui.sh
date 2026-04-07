#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="$("$ROOT_DIR/runtime/.venv/bin/python" - <<'PY'
from vmlx_station_daemon.config import AppPaths, load_config

config = load_config(AppPaths.default())
print(f"http://{config.open_webui.host}:{config.open_webui.port}")
PY
)"

echo "--- Open WebUI ---"
echo "base_url=$BASE_URL"
if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  curl -fsS "$BASE_URL/health"
  echo
else
  curl -fsS -I "$BASE_URL/" | sed -n '1,5p'
fi
echo
