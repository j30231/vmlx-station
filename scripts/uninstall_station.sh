#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/uninstall_menu_bar.sh" || true
"$ROOT_DIR/scripts/uninstall_daemon.sh" || true

echo
echo "vMLX Station uninstalled."
