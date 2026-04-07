#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_SUPPORT_DIR="${APP_SUPPORT_DIR:-$HOME/Library/Application Support/vmlx-station}"
BIN_DIR="$APP_SUPPORT_DIR/bin"
LOG_DIR="$APP_SUPPORT_DIR/logs"
CONFIG_DIR="$APP_SUPPORT_DIR"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LABEL="com.vmlxstation.daemon"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$LABEL.plist"
WRAPPER_PATH="$BIN_DIR/run_vmlx_station_daemon.sh"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/runtime/.venv}"

mkdir -p "$BIN_DIR" "$LOG_DIR" "$CONFIG_DIR" "$LAUNCH_AGENTS_DIR"

"$ROOT_DIR/scripts/bootstrap_runtime.sh"

if [ ! -f "$APP_SUPPORT_DIR/config.yaml" ]; then
  cp "$ROOT_DIR/config/example-config.yaml" "$APP_SUPPORT_DIR/config.yaml"
fi

cat >"$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$ROOT_DIR"
VENV_DIR="\${VENV_DIR:-$ROOT_DIR/runtime/.venv}"
if [ ! -x "\$VENV_DIR/bin/python" ]; then
  echo "Runtime venv not found: \$VENV_DIR" >&2
  exit 1
fi
export PYTHONPATH="$ROOT_DIR/runtime/src:\${PYTHONPATH:-}"
exec "\$VENV_DIR/bin/python" -m vmlx_station_daemon.cli
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
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/daemon.launchd.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/daemon.launchd.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$LABEL" >/dev/null 2>&1 || true
launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

CONTROL_BASE_URL="$("$VENV_DIR/bin/python" - <<'PY'
from vmlx_station_daemon.config import AppPaths, load_config

config = load_config(AppPaths.default())
print(f"http://{config.control_api.host}:{config.control_api.port}")
PY
)"

for _ in $(seq 1 30); do
  if curl -fsS "$CONTROL_BASE_URL/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "$CONTROL_BASE_URL/health" >/dev/null 2>&1; then
  echo "Daemon did not become healthy: $CONTROL_BASE_URL/health" >&2
  exit 1
fi

echo "Installed and started $LABEL"
echo "Config: $APP_SUPPORT_DIR/config.yaml"
echo "Check with: $ROOT_DIR/scripts/check_daemon.sh"
