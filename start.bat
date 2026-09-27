@echo off
rem ============================================
rem  Little Planet Cyber - one click start (Windows)
rem  Starts the server and opens the game page.
rem ============================================
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo   Node.js not found. Please install it first: https://nodejs.org
  echo.
  pause
  exit /b 1
)

echo.
echo   Starting server...
start "" "http://localhost:8765/"
node server\server.js
