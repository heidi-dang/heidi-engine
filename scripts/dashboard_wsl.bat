@echo off
REM scripts/dashboard_wsl.bat — simple launcher to run the dashboard inside WSL
REM Usage: double-click this file in Windows Explorer or run from cmd/powershell

:: Change this path if your WSL home/project path differs
set REPO_PATH=/home/heidi/ai/heidi-engine







pause >nulecho Dashboard launcher finished. Press any key to close...echo.wsl bash -lc "cd %REPO_PATH% && if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi && python scripts/menu.py"n:: Activate virtualenv (if present) and run the dashboard script inside WSL