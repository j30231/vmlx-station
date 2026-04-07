#!/usr/bin/env bash
set -euo pipefail

LABEL="com.vmlxstation.menu-bar"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"

echo "--- launchctl list ---"
launchctl list | rg "$LABEL" || true
echo

echo "--- launchctl print ---"
launchctl print "gui/$(id -u)/$LABEL" || true
echo

echo "--- plist ---"
if [ -f "$PLIST_PATH" ]; then
  cat "$PLIST_PATH"
else
  echo "Missing: $PLIST_PATH"
fi
