#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
PYTHON="${PYTHON:-python3}"
DEPS=(pip pyyaml requests beautifulsoup4 openpyxl pytest)

cd "$ROOT"

if [[ ! -d "$VENV" ]]; then
  echo "Creating virtualenv at $VENV"
  "$PYTHON" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "Upgrading dependencies…"
python -m pip install --upgrade "${DEPS[@]}"

echo
echo "Done. Activate with:"
echo "  source .venv/bin/activate"
