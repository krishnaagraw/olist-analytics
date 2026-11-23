@echo off
REM Double-click this file (Windows). It creates a virtual environment, installs
REM packages, builds the data from data\raw and opens the dashboard.
cd /d "%~dp0"
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -q -r requirements-dev.txt
python run.py %*
pause
