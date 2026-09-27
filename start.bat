@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment and installing packages...
  py -3 -m venv .venv 2>nul
  if not exist ".venv\Scripts\python.exe" python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo.
echo When Streamlit prints a Local URL, open it in your browser.
echo Usually: http://localhost:8501
echo.
".venv\Scripts\python.exe" -m streamlit run src\app.py
