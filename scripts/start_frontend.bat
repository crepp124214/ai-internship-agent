@echo off
setlocal

set "ROOT=%~dp0.."
set "FRONTEND_DIR=%ROOT%\frontend"

if not exist "%FRONTEND_DIR%\package.json" (
  echo [ERROR] Frontend package.json not found: "%FRONTEND_DIR%\package.json"
  exit /b 1
)

cd /d "%FRONTEND_DIR%"
start "AIIA Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort"

endlocal
exit /b 0
