@echo off
title ZKTeco K50 - Manual Attendance Sync
cd /d "%~dp0"
python main.py --sync-once
pause
