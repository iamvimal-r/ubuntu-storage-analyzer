#!/usr/bin/env bash
# setup.sh — One-shot Ubuntu venv setup and launch script.
# Usage: bash setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Ubuntu Storage & Memory Analyzer — Setup ==="
echo ""

# ── Detect python3 ────────────────────────────────────────────────────────────
PY=$(command -v python3.12 || command -v python3.11 || command -v python3 || true)
if [[ -z "$PY" ]]; then
    echo "ERROR: python3 not found. Install it with: sudo apt install python3"
    exit 1
fi
echo "Using Python: $PY ($($PY --version))"

# ── Create venv ───────────────────────────────────────────────────────────────
if [[ ! -d "venv" ]]; then
    echo "Creating virtual environment…"
    "$PY" -m venv venv
else
    echo "Virtual environment already exists."
fi

# ── Activate and install ──────────────────────────────────────────────────────
# shellcheck disable=SC1091
source venv/bin/activate

echo "Upgrading pip…"
pip install --quiet --upgrade pip

echo "Installing dependencies…"
pip install --quiet -r requirements.txt

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To launch the application:"
echo "  source venv/bin/activate && python main.py"
echo ""
echo "To run tests:"
echo "  source venv/bin/activate && python -m pytest tests/ -v"
echo ""
