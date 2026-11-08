@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py
) else (
    py -3.11 run.py
)

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
