#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/runtime/.venv}"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "Runtime venv not found: $VENV_DIR" >&2
  echo "Create it with:" >&2
  echo "  cd '$ROOT_DIR/runtime' && python3 -m venv .venv && source .venv/bin/activate && pip install -e ." >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/runtime/src:${PYTHONPATH:-}"
exec "$VENV_DIR/bin/python" -m vmlx_station_daemon.cli

