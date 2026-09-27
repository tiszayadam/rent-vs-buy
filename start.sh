#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ -x .venv/Scripts/python.exe ]]; then
  PY=".venv/Scripts/python.exe"
elif [[ -x .venv/bin/python ]]; then
  PY=".venv/bin/python"
else
  echo "No virtualenv found. Create one and install requirements first:" >&2
  echo "  python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt" >&2
  exit 1
fi

exec "$PY" -m streamlit run app.py
