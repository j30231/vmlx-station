#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/install_daemon.sh"
"$ROOT_DIR/scripts/install_open_webui.sh"
"$ROOT_DIR/scripts/install_menu_bar.sh"

echo
echo "vMLX Station installed."
echo "Daemon check: $ROOT_DIR/scripts/check_daemon.sh"
echo "Open WebUI check: $ROOT_DIR/scripts/check_open_webui.sh"
echo "Menu bar check: $ROOT_DIR/scripts/check_menu_bar.sh"
