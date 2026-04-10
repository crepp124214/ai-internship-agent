@echo off
setlocal EnableDelayedExpansion

REM ======================================
REM AI Internship Agent - One-click Dev Start (Windows)
REM Starts backend + frontend in separate windows
REM ======================================

set "ROOT=%~dp0.."
set "BACKEND_DIR=%ROOT%"
set "FRONTEND_DIR=%ROOT%\frontend"
set "VENV_DIR=%ROOT%\.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

if not exist "%FRONTEND_DIR%" (
  echo [ERROR] Frontend directory not found: "%FRONTEND_DIR%"
  pause
  exit /b 1
)

if not exist "%VENV_DIR%" (
  echo [INFO] Python virtual env not found. Creating .venv ...
  cd /d "%BACKEND_DIR%"
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment. Ensure Python is installed.
    pause
    exit /b 1
  )
)

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python executable not found in .venv: "%PYTHON_EXE%"
  pause
  exit /b 1
)

if not exist "%ROOT%\.env" (
  if exist "%ROOT%\.env.example" (
    echo [INFO] .env not found, creating from .env.example ...
    copy /Y "%ROOT%\.env.example" "%ROOT%\.env" >nul
  ) else (
    echo [WARN] .env and .env.example both missing. Please create .env manually.
  )
)

echo [INFO] Cleaning stale dev processes...
call "%~dp0stop_dev.bat" >nul 2>&1

echo [INFO] Installing backend dependencies (first run may take a while)...
cd /d "%BACKEND_DIR%"
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Backend dependency installation failed.
  pause
  exit /b 1
)

echo [INFO] Installing frontend dependencies (first run may take a while)...
cd /d "%FRONTEND_DIR%"
call npm install
if errorlevel 1 (
  echo [ERROR] Frontend dependency installation failed.
  pause
  exit /b 1
)

echo [INFO] Starting backend on http://127.0.0.1:8000 ...
start "AIIA Backend" cmd /k "cd /d "%BACKEND_DIR%" && set APP_ENV=development && set DATABASE_URL=sqlite:///./data/app.db && "%PYTHON_EXE%" -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload"

echo [INFO] Starting frontend on http://127.0.0.1:5173 ...
start "AIIA Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort"

echo.
echo ======================================
echo Started!
echo Backend : http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo ======================================
echo Tip: close the two opened terminal windows to stop services.

endlocal
exit /b 0
