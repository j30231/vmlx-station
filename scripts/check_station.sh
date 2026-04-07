#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Daemon ==="
"$ROOT_DIR/scripts/check_daemon.sh" || true
echo
echo "=== Open WebUI ==="
"$ROOT_DIR/scripts/check_open_webui.sh" || true
echo
echo "=== Menu Bar ==="
"$ROOT_DIR/scripts/check_menu_bar.sh" || true
