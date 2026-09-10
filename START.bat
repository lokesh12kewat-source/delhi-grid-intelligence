@echo off
title Vidyut AI - Starting Servers
color 0A
echo.
echo  ========================================
echo    Vidyut AI - Starting Local Servers
echo  ========================================
echo.

REM Start Backend in new window
echo  [1/2] Starting Backend on http://localhost:8000 ...
start "Vidyut AI - Backend" cmd /k "cd /d %~dp0backend && set PYTHONIOENCODING=utf-8 && uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak > nul

REM Start Frontend in new window
echo  [2/2] Starting Frontend on http://localhost:5173 ...
start "Vidyut AI - Frontend" cmd /k "cd /d %~dp0frontend && set PATH=C:\nodejs\node-v20.15.0-win-x64;%PATH% && npm run dev"

REM Wait for frontend to start
timeout /t 5 /nobreak > nul

REM Open browser
echo.
echo  Opening browser...
start http://localhost:5173

echo.
echo  ========================================
echo    Both servers are running!
echo    Frontend : http://localhost:5173
echo    Backend  : http://localhost:8000
echo    
echo    Close the two terminal windows to stop.
echo  ========================================
echo.
pause
