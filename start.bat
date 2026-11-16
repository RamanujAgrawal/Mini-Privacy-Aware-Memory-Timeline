@echo off
title Chronis Privacy-Aware Memory Timeline
echo =================================================================
echo        CHRONIS • Privacy-Aware Memory Timeline Launcher
echo =================================================================
echo.

cd /d "%~dp0"

:: 1. Detect Python from virtual environment or system
set PYTHON_CMD=python
if exist "..\.venv\Scripts\python.exe" (
    set PYTHON_CMD=..\.venv\Scripts\python.exe
) else if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

echo [1/3] Using Python: %PYTHON_CMD%

:: 2. Seed database
echo [2/3] Initializing and seeding database...
%PYTHON_CMD% backend/seed.py

:: 3. Open browser after 2 seconds
start "" http://127.0.0.1:8000/

:: 4. Launch server
echo [3/3] Launching server on http://127.0.0.1:8000 ...
echo Press CTRL+C to stop the server.
echo.
%PYTHON_CMD% run.py
pause
