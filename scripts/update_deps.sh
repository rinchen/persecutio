#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
PYTHON="${PYTHON:-python3}"

cd "$ROOT"

if [[ ! -d "$VENV" ]]; then
  echo "Creating virtualenv at $VENV"
  "$PYTHON" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "Installing from requirements.txt…"
python -m pip install --upgrade pip
python -m pip install -r "$ROOT/requirements.txt"

echo
echo "Done. Activate with:"
echo "  source .venv/bin/activate"
