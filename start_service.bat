@echo off
title Start Biometric Sync Windows Service
cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script must be Run as Administrator.
    echo Right-click on this file and select "Run as administrator".
    pause
    exit /b 1
)

echo Starting BiometricSyncAgent Windows Service...
net start BiometricSyncAgent
echo.
sc query BiometricSyncAgent
pause
