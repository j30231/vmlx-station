#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${VMLX_STATION_API:-http://127.0.0.1:18100}"

echo "--- /health ---"
curl -fsS "$BASE_URL/health"
echo
echo "--- /api/status ---"
curl -fsS "$BASE_URL/api/status"
echo
echo "--- /api/models ---"
python3 - <<PY
import json
import urllib.request

payload = json.load(urllib.request.urlopen("${BASE_URL}/api/models"))
print(f"count={payload['count']}")
for item in payload["items"][:10]:
    print(f"{item['id']} :: {item['engine']} :: {item['name']}")
PY
