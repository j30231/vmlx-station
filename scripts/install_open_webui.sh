#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_SUPPORT_DIR="${APP_SUPPORT_DIR:-$HOME/Library/Application Support/vmlx-station}"
OPEN_WEBUI_DIR="$APP_SUPPORT_DIR/open-webui"
OPEN_WEBUI_VENV_DIR="${OPEN_WEBUI_VENV_DIR:-$OPEN_WEBUI_DIR/.venv}"
DATA_DIR="$OPEN_WEBUI_DIR/data"
BIN_DIR="$APP_SUPPORT_DIR/bin"
LOG_DIR="$APP_SUPPORT_DIR/logs"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LABEL="com.vmlxstation.open-webui"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$LABEL.plist"
WRAPPER_PATH="$BIN_DIR/run_open_webui.sh"

mkdir -p "$OPEN_WEBUI_DIR" "$DATA_DIR" "$BIN_DIR" "$LOG_DIR" "$LAUNCH_AGENTS_DIR"

"$ROOT_DIR/scripts/bootstrap_runtime.sh"

python3.11 -m venv "$OPEN_WEBUI_VENV_DIR"
source "$OPEN_WEBUI_VENV_DIR/bin/activate"
python -m pip install -U pip wheel setuptools open-webui

eval "$("$ROOT_DIR/runtime/.venv/bin/python" - <<'PY'
from vmlx_station_daemon.config import AppPaths, load_config

config = load_config(AppPaths.default())
runtime = config.runtime
webui = config.open_webui
api_key = runtime.api_key or "vmlx-station-local"
print(f'OPEN_WEBUI_HOST="{webui.host}"')
print(f'OPEN_WEBUI_PORT="{webui.port}"')
print(f'OPEN_WEBUI_BASE_URL="http://{webui.host}:{webui.port}"')
print(f'OPENAI_API_BASE_URL_VALUE="http://{runtime.host}:{runtime.port}/v1"')
print(f'OPENAI_API_KEY_VALUE="{api_key}"')
PY
)"

cat >"$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
VENV_DIR="$OPEN_WEBUI_VENV_DIR"
DATA_DIR="$DATA_DIR"
if [ ! -x "\$VENV_DIR/bin/open-webui" ]; then
  echo "open-webui binary not found: \$VENV_DIR/bin/open-webui" >&2
  exit 1
fi
export DATA_DIR="\$DATA_DIR"
export OPENAI_API_BASE_URL="$OPENAI_API_BASE_URL_VALUE"
export OPENAI_API_BASE_URLS="$OPENAI_API_BASE_URL_VALUE"
export OPENAI_API_KEY="$OPENAI_API_KEY_VALUE"
export OPENAI_API_KEYS="$OPENAI_API_KEY_VALUE"
export BYPASS_EMBEDDING_AND_RETRIEVAL="true"
export RAG_EMBEDDING_MODEL=""
export RAG_RERANKING_MODEL=""
export ENABLE_RAG_HYBRID_SEARCH="false"
export RAG_EMBEDDING_MODEL_AUTO_UPDATE="false"
export AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST="3"
export USER_AGENT="vmlx-station"
exec "\$VENV_DIR/bin/open-webui" serve --host "$OPEN_WEBUI_HOST" --port "$OPEN_WEBUI_PORT"
EOF
chmod +x "$WRAPPER_PATH"

cat >"$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>WorkingDirectory</key>
  <string>$APP_SUPPORT_DIR</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$WRAPPER_PATH</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <dict>
    <key>SuccessfulExit</key>
    <false/>
  </dict>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/open-webui.launchd.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/open-webui.launchd.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$LABEL" >/dev/null 2>&1 || true
launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

for _ in $(seq 1 60); do
  if curl -fsS "$OPEN_WEBUI_BASE_URL/health" >/dev/null 2>&1 || curl -fsS "$OPEN_WEBUI_BASE_URL/" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "$OPEN_WEBUI_BASE_URL/health" >/dev/null 2>&1 && ! curl -fsS "$OPEN_WEBUI_BASE_URL/" >/dev/null 2>&1; then
  echo "Open WebUI did not become healthy: $OPEN_WEBUI_BASE_URL" >&2
  exit 1
fi

echo "Installed and started $LABEL"
echo "Open WebUI: $OPEN_WEBUI_BASE_URL"
echo "Connected backend: $OPENAI_API_BASE_URL_VALUE"
echo "Check with: $ROOT_DIR/scripts/check_open_webui.sh"
