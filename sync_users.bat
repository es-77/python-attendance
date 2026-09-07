@echo off
title ZKTeco K50 - Sync Users to Machine Memory
cd /d "%~dp0"
echo ============================================================
echo   Syncing Mapped ERP Users to ZKTeco K50 Device Memory
echo ============================================================
echo.
python main.py --sync-users
echo.
pause
