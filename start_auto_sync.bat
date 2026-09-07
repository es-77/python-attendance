@echo off
title ZKTeco K50 - Auto Attendance Sync Agent
cd /d "%~dp0"
echo ============================================================
echo   Starting ZKTeco K50 Auto Attendance Sync Agent
echo   Syncs attendance every 60 seconds automatically.
echo   Press Ctrl+C to stop.
echo ============================================================
echo.
python main.py
pause
