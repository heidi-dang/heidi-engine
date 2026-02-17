@echo off
setlocal EnableExtensions

REM ===== Optional overrides =====
REM set HEIDI_WSL_DISTRO=Ubuntu-24.04
REM set HEIDI_WSL_REPO=~/work/heidi-engine
REM ==============================

if "%HEIDI_WSL_REPO%"=="" set "HEIDI_WSL_REPO=~/work/heidi-engine"

set "DISTRO_ARGS="
if not "%HEIDI_WSL_DISTRO%"=="" set "DISTRO_ARGS=-d %HEIDI_WSL_DISTRO%"

echo.
echo [heidi-engine] Launching dashboard in WSL...
echo   Distro: %HEIDI_WSL_DISTRO%
echo   Repo  : %HEIDI_WSL_REPO%
echo.

wsl.exe %DISTRO_ARGS% -- bash -lc "set -e; \
  echo '[WSL] user='$(whoami) 'home='$HOME; \
  if [ ! -d %HEIDI_WSL_REPO% ]; then \
    echo '[ERROR] Repo path not found: %HEIDI_WSL_REPO%'; \
    echo '        Tip: set HEIDI_WSL_REPO to the correct folder.'; \
    echo '        Listing ~/work:'; ls -la ~/work || true; \
    exit 2; \
  fi; \
  cd %HEIDI_WSL_REPO%; \
  command -v python3 >/dev/null || { echo '[ERROR] python3 not found in WSL'; exit 3; }; \
  [ -d .venv ] || python3 -m venv .venv; \
  . .venv/bin/activate; \
  python -m pip install -U pip; \
  pip install -e .; \
  MOD=$(python -c \"import importlib.util as u; mods=['heidi_engine.dashboard','autotrain.dashboard']; print(next((m for m in mods if u.find_spec(m)), ''))\"); \
  if [ -z \"$MOD\" ]; then echo '[ERROR] No dashboard module found (heidi_engine.dashboard/autotrain.dashboard)'; exit 4; fi; \
  echo '[WSL] starting:' python -m \"$MOD\"; \
  exec python -m \"$MOD\" \
"

echo.
echo [heidi-engine] Exit code: %errorlevel%
echo.
pause
endlocal
