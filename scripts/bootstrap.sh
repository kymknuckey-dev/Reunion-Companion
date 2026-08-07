#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

echo
echo "Reunion Companion development environment is ready."
echo "Activate it later with: source .venv/bin/activate"
