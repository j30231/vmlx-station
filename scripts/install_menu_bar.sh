#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_SUPPORT_DIR="${APP_SUPPORT_DIR:-$HOME/Library/Application Support/vmlx-station}"
BIN_DIR="$APP_SUPPORT_DIR/bin"
LOG_DIR="$APP_SUPPORT_DIR/logs"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LABEL="com.vmlxstation.menu-bar"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$LABEL.plist"
WRAPPER_PATH="$BIN_DIR/run_vmlx_station_menu_bar.sh"
BINARY_PATH="$BIN_DIR/VmlxStationMenuBar"
BUILD_CONFIGURATION="${BUILD_CONFIGURATION:-debug}"

mkdir -p "$BIN_DIR" "$LOG_DIR" "$LAUNCH_AGENTS_DIR"

swift build --configuration "$BUILD_CONFIGURATION" --product VmlxStationMenuBar

BUILT_BINARY="$ROOT_DIR/.build/$BUILD_CONFIGURATION/VmlxStationMenuBar"
if [ ! -x "$BUILT_BINARY" ]; then
  echo "Built binary not found: $BUILT_BINARY" >&2
  exit 1
fi

cp "$BUILT_BINARY" "$BINARY_PATH"
chmod +x "$BINARY_PATH"

cat >"$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
BIN_PATH="$BINARY_PATH"
if [ ! -x "\$BIN_PATH" ]; then
  echo "Menu bar binary not found: \$BIN_PATH" >&2
  exit 1
fi
exec "\$BIN_PATH"
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
  <key>LimitLoadToSessionType</key>
  <array>
    <string>Aqua</string>
  </array>
  <key>ProcessType</key>
  <string>Interactive</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <dict>
    <key>SuccessfulExit</key>
    <false/>
  </dict>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/menu-bar.launchd.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/menu-bar.launchd.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$LABEL" >/dev/null 2>&1 || true
launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "Installed and started $LABEL"
echo "Binary: $BINARY_PATH"
echo "Check with: $ROOT_DIR/scripts/check_menu_bar.sh"
