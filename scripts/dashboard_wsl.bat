@echo off
setlocal EnableExtensions

REM Optional: set these before running, or edit them here
REM set HEIDI_WSL_DISTRO=Ubuntu-24.04
REM set HEIDI_WSL_REPO=~/work/heidi-engine

if "%HEIDI_WSL_REPO%"=="" set "HEIDI_WSL_REPO=~/work/heidi-engine"

set "WSL=wsl"
if not "%HEIDI_WSL_DISTRO%"=="" set "WSL=wsl -d %HEIDI_WSL_DISTRO%"

REM Prefer Windows Terminal if available
where wt >nul 2>nul
if %errorlevel%==0 (
  wt -w 0 new-tab --title "heidi-engine dashboard (WSL)" cmd /c "%WSL% -- bash -lc \"set -e; cd %HEIDI_WSL_REPO%; python3 -m venv .venv >/dev/null 2>&1 || true; source .venv/bin/activate; python -m pip install -U pip >/dev/null; pip install -e . >/dev/null; export HEIDI_RUNTIME=\$HOME/.local/heidi-engine; mkdir -p \$HEIDI_RUNTIME; python -m heidi_engine.dashboard\""
) else (
  %WSL% -- bash -lc "set -e; cd %HEIDI_WSL_REPO%; python3 -m venv .venv >/dev/null 2>&1 || true; source .venv/bin/activate; python -m pip install -U pip >/dev/null; pip install -e . >/dev/null; export HEIDI_RUNTIME=\$HOME/.local/heidi-engine; mkdir -p \$HEIDI_RUNTIME; python -m heidi_engine.dashboard"
)

endlocal
