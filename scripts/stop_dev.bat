@echo off
setlocal

REM ======================================
REM AI Internship Agent - One-click Dev Stop (Windows)
REM Stops backend/frontend started by start_dev.bat
REM ======================================

echo [INFO] Stopping windows by title...
taskkill /FI "WINDOWTITLE eq AIIA Backend" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AIIA Frontend" /T /F >nul 2>&1

echo [INFO] Stopping common dev ports (8000/5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo.
echo ======================================
echo Done. Backend/Frontend should be stopped.
echo ======================================

endlocal
exit /b 0
