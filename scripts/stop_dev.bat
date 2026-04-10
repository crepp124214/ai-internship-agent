@echo off
setlocal

REM ======================================
REM AI Internship Agent - One-click Dev Stop (Windows)
REM Stops backend/frontend started by start_dev.bat
REM ======================================

echo [INFO] Stopping windows by title...
taskkill /FI "WINDOWTITLE eq AIIA Backend" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AIIA Frontend" /T /F >nul 2>&1

echo [INFO] Stopping processes on common dev ports (8000/5173/5174)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5174') do taskkill /PID %%a /F >nul 2>&1

echo [INFO] Stopping stale uvicorn/vite command-line processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$patterns = @('uvicorn src.main:app','vite --host 127.0.0.1 --port 5173','npm run dev -- --host 127.0.0.1 --port 5173');" ^
  "$procs = Get-CimInstance Win32_Process | Where-Object { $cmd = $_.CommandLine; $cmd -and (($patterns | Where-Object { $cmd -like ('*' + $_ + '*') }).Count -gt 0) };" ^
  "foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo.
echo ======================================
echo Done. Backend/Frontend should be stopped.
echo ======================================

endlocal
exit /b 0
