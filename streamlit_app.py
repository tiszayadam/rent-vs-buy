"""Root Streamlit entry so Community Cloud / the Deploy button see a GitHub app at the repo root."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(_SRC))
runpy.run_path(str(_SRC / "app.py"), run_name="__main__")
