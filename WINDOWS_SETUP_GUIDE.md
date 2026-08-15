# ZKTeco K50 Biometric Sync Agent - Windows Installation & Management Guide

This document provides a step-by-step guide to installing, configuring, and running the ZKTeco K50 Biometric Attendance Sync Agent as an automatic background service on Windows.

---

## 1. System Requirements
- **Operating System**: Windows 10 / Windows 11 / Windows Server
- **Python**: Version 3.8 or higher (Python 3.12 recommended)
- **Network**: ZKTeco K50 machine connected on local TCP/IP network (Default: `192.168.1.201:4370`)
- **ERP Connection**: Network or Internet connectivity to your Laravel ERP API endpoint

---

## 2. Step-by-Step Setup Instructions

### Step 1: Open PowerShell as Administrator
Right-click on the **Windows Start Menu** button, select **PowerShell (Admin)** or **Terminal (Admin)**.

### Step 2: Navigate to the Agent Directory
```powershell
cd C:\laragon\www\school\python
```

### Step 3: Configure `.env` Environment File
Create or open the `.env` file in the `C:\laragon\www\school\python` folder and configure your device and ERP API details:
```ini
DEVICE_NAME=K50-MAIN
DEVICE_IP=192.168.1.201
DEVICE_PORT=4370
DEVICE_TIMEOUT=10

# ERP API Endpoint URL (Replace with your actual domain or local address)
ERP_API_URL=http://localhost:8000/api/v1/emmanuel

# Biometric Device API Bearer Token (Generated in Laravel biometric_devices table)
ERP_API_TOKEN=test-token-k50

# Synchronization Interval (in seconds)
SYNC_INTERVAL=60

LOCAL_DATABASE=biometric_agent.db
LOG_LEVEL=INFO
```

### Step 4: Install Dependencies System-Wide
Run the following command in Administrator PowerShell to ensure the Windows Service account (`LocalSystem`) has permission to access all required Python libraries:
```powershell
pip install --ignore-installed --no-user pywin32 requests python-dotenv pyzk pytest
```

### Step 5: Configure Machine-Wide PYTHONPATH
Set the machine environment variable so Windows Service host (`pythonservice.exe`) can locate the agent modules:
```powershell
[Environment]::SetEnvironmentVariable("PYTHONPATH", "C:\laragon\www\school\python", "Machine")
```

### Step 6: Install the Windows Background Service
Run the automated installer script:
```powershell
python install_service.py
```

---

## 3. Starting & Managing the Service

### Start the Service
```powershell
net start BiometricSyncAgent
```

### Stop the Service
```powershell
net stop BiometricSyncAgent
```

### Check Service Status in PowerShell
```powershell
Get-Service BiometricSyncAgent
```

### Verify Service in Windows Services GUI
1. Press `Windows Key + R`, type **`services.msc`**, and press Enter.
2. Look for **`ZKTeco K50 Biometric Sync Agent`**.
3. Verify that **Status** is `Running` and **Startup Type** is `Automatic`.

---

## 4. Useful Maintenance & Diagnostic Commands

### Run Diagnostics Test
Verifies network connectivity to K50, database queue integrity, and ERP API authentication:
```powershell
python main.py --test
```

### Run One-Time Manual Sync
Pulls logs from K50 and pushes unsynced records to Laravel ERP once:
```powershell
python main.py --sync-once
```

### Print Local SQLite Queue Status
```powershell
python main.py --status
```

### Run Service in Interactive Debug Mode
```powershell
$env:PYTHONPATH = "C:\laragon\www\school\python"
& "C:\Program Files\Python312\pythonservice.exe" -debug BiometricSyncAgent
```

### Uninstall the Service
```powershell
python uninstall_service.py
```

---

## 5. Log Files & Troubleshooting

- **Agent Activity Log**: Stores all sync cycles, punch reads, and API responses:
  `C:\laragon\www\school\python\logs\agent.log`
- **Service Startup Log**: Stores low-level service wrapper initialization tracebacks:
  `C:\laragon\www\school\python\logs\service_startup.log`

### Common Solutions:
1. **Service fails to start (Error 3547 / Code 1)**:
   Ensure Step 5 was executed (`[Environment]::SetEnvironmentVariable("PYTHONPATH", "C:\laragon\www\school\python", "Machine")`).
2. **K50 Disconnected / Port Error**:
   Verify physical network cabling and ping the device IP: `ping 192.168.1.201`.
3. **ERP Authentication 401 Error**:
   Ensure `ERP_API_TOKEN` matches the token configured on the Laravel ERP backend `biometric_devices` table.
