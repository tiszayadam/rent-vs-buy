#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ -x .venv/Scripts/python.exe ]]; then
  PY=".venv/Scripts/python.exe"
elif [[ -x .venv/bin/python ]]; then
  PY=".venv/bin/python"
else
  echo "Creating virtual environment and installing packages..."
  python -m venv .venv
  if [[ -x .venv/Scripts/python.exe ]]; then
    PY=".venv/Scripts/python.exe"
  else
    PY=".venv/bin/python"
  fi
  "$PY" -m pip install -r requirements.txt
fi

echo "When Streamlit prints a Local URL, open it in your browser."
echo "Usually: http://localhost:8501"
exec "$PY" -m streamlit run streamlit_app.py
