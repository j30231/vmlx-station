#!/usr/bin/env bash
set -euo pipefail

APP_SUPPORT_DIR="${APP_SUPPORT_DIR:-$HOME/Library/Application Support/vmlx-station}"
BIN_DIR="$APP_SUPPORT_DIR/bin"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LABEL="com.vmlxstation.menu-bar"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$LABEL.plist"
WRAPPER_PATH="$BIN_DIR/run_vmlx_station_menu_bar.sh"
BINARY_PATH="$BIN_DIR/VmlxStationMenuBar"

launchctl bootout "gui/$(id -u)" "$LABEL" >/dev/null 2>&1 || true
launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true

rm -f "$PLIST_PATH" "$WRAPPER_PATH" "$BINARY_PATH"

echo "Uninstalled $LABEL"
