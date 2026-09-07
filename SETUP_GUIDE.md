# ZKTeco K50 & Next Gen Service ERP - Complete Setup & Management Guide

This comprehensive guide details how to install, configure, test, and run the **Biometric Attendance & User Sync Agent** for the ZKTeco K50 device and Next Gen Service ERP.

---

## 1. System Architecture & Workflow

```
┌──────────────────────────┐          TCP/IP (Port 4370)          ┌──────────────────────────┐
│                          │ ◄──────────────────────────────────► │                          │
│     ZKTeco K50 Device    │   1. Push User Profiles to K50       │    Python Sync Agent     │
│   (IP: 192.168.18.201)   │   2. Pull Fingerprint Punches Logs   │   (Local School PC)      │
│                          │                                      │   - Local SQLite Queue   │
└──────────────────────────┘                                      └─────────────┬────────────┘
                                                                                │
                                                                                │ HTTPS POST / GET
                                                                                │ (Bearer Token)
                                                                                ▼
                                                                  ┌──────────────────────────┐
                                                                  │  Next Gen Service ERP    │
                                                                  │  (School Cloud Portal)   │
                                                                  └──────────────────────────┘
```

1. **User Synchronization**: Mapped teachers/staff in ERP are automatically registered on the physical K50 machine memory with their designated Biometric IDs and Names.
2. **Attendance Synchronization**: Punches from K50 are pulled every 60 seconds, stored safely in a local offline-first SQLite database (`biometric_agent.db`), and uploaded to Next Gen Service ERP.

---

## 2. Prerequisites & Python Installation

### A. Install Python
Ensure Python **3.8+** (Python 3.12 recommended) is installed on the school computer.
During Python setup, ensure **"Add Python to PATH"** is checked.

### B. Install Python Dependencies
Open PowerShell or Command Prompt inside `C:\laragon\www\school\python` and run:
```cmd
pip install requests python-dotenv pyzk pywin32 pytest
```
Or install via requirements file:
```cmd
pip install -r requirements.txt
```

---

## 3. Configuration (.env)

Open `C:\laragon\www\school\python\.env` and configure your settings:

```ini
# Biometric Agent Configuration

# Physical K50 Machine Settings
DEVICE_NAME=K50-MAIN
DEVICE_IP=192.168.18.201
DEVICE_PORT=4370
DEVICE_TIMEOUT=10

# Next Gen Service ERP API Endpoint
ERP_API_URL=https://next-gen-service.com/api/v1/francis

# Device Bearer Token (Configured in ERP Biometric Devices)
ERP_API_TOKEN=test-token-k50

# Attendance Sync Interval in seconds (e.g., 60 = 1 minute)
SYNC_INTERVAL=60

# User Sync Interval in seconds (e.g., 120 = 2 minutes)
USER_SYNC_INTERVAL=120

# Local SQLite Offline Cache Database
LOCAL_DATABASE=biometric_agent.db

# Logging Level (INFO / DEBUG / WARNING / ERROR)
LOG_LEVEL=INFO
```

---

## 4. Diagnostics & Health Check

Before starting auto-sync, always run the built-in diagnostic test to verify all connections:

```cmd
python main.py --test
```

### What this test checks:
1. **Config Validation**: Checks if `.env` settings are properly defined.
2. **SQLite Database**: Verifies local queue table structure.
3. **Network Reachability**: Pings and opens TCP port `4370` on the K50 IP.
4. **ZKTeco Protocol Handshake**: Connects to the machine and reads hardware serial number, model, and firmware.
5. **Attendance Log Reading**: Confirms raw attendance logs can be read from device memory.
6. **Next Gen Service ERP API Connection**: Sends a test heartbeat and validates the `ERP_API_TOKEN`.

If all items output `[OK]`, your system is production-ready.

---

## 5. User Synchronization (ERP ➔ K50 Machine)

### How User Sync Works:
- The agent fetches the list of mapped teachers and staff from Next Gen Service ERP.
- Compares it with users currently in the K50 device memory.
- If a user is missing or their name has changed, it writes `ID` and `Name` into the K50 memory.

### To Manually Trigger User Sync:
Double-click `sync_users.bat` or run in terminal:
```cmd
python main.py --sync-users
```

### Enrolling Fingerprints on the Machine:
1. After running User Sync, go to the physical K50 machine.
2. Press **M/OK** on the machine to open the menu.
3. Select **User Mgt** ➔ **All Users**.
4. You will see the synced User IDs and Names already listed.
5. Select the user and choose **Fingerprint** to enroll their finger.

---

## 6. Attendance Synchronization (K50 Machine ➔ ERP)

### How Attendance Sync Works:
- The agent connects to the K50 and downloads raw attendance records.
- Saves new records in `biometric_agent.db` (preventing duplicate uploads).
- Sends new records to Next Gen Service ERP (`/biometric/attendance/sync`).
- ERP processes the punches and marks teacher/student attendance.

### To Manually Run One-Time Attendance Sync:
Double-click `sync_once.bat` or run in terminal:
```cmd
python main.py --sync-once
```

### To Check Local Database Queue Counts:
```cmd
python main.py --status
```

---

## 7. Running Automatic Attendance & User Sync

You can run auto-sync in two modes:

### Option A: 1-Click Interactive Mode (Recommended)
Double-click **`start_auto_sync.bat`** in `C:\laragon\www\school\python`.
- A window will stay open showing live logs.
- Attendance is checked and synced every **60 seconds**.
- New ERP users are synced every **2 minutes**.
- Press `Ctrl + C` anytime to safely stop.

---

### Option B: 24/7 Silent Windows Background Service
To make the agent run automatically in the background on Windows startup without needing a window open:

1. **Install the Windows Service** (Once):
   - Open Command Prompt or PowerShell as **Administrator**:
   ```cmd
   cd C:\laragon\www\school\python
   python install_service.py
   ```
2. **Start the Service**:
   - Right-click `start_service.bat` and select **Run as Administrator**, or run:
   ```cmd
   net start BiometricSyncAgent
   ```
3. **Stop the Service**:
   - Right-click `stop_service.bat` and select **Run as Administrator**, or run:
   ```cmd
   net stop BiometricSyncAgent
   ```

---

## 8. Batch Shortcuts Reference

All scripts are in `C:\laragon\www\school\python\`:

| Batch File | Function | How to Run |
| :--- | :--- | :--- |
| `start_auto_sync.bat` | Starts continuous auto attendance & user sync loop | Double-click |
| `sync_users.bat` | Syncs mapped users from ERP to K50 machine | Double-click |
| `sync_once.bat` | Runs a single manual attendance sync cycle | Double-click |
| `start_service.bat` | Starts the 24/7 Windows Background Service | Right-click ➔ Run as Admin |
| `stop_service.bat` | Stops the 24/7 Windows Background Service | Right-click ➔ Run as Admin |

---

## 9. Troubleshooting & FAQ

### 1. Error: `ZKNetworkError - can't reach device (ping 192.168.18.201)`
- **Cause**: The Ethernet cable is unplugged, or the K50 machine is powered off / on a different IP.
- **Solution**: 
  - Ensure the Ethernet cable is firmly plugged into both the K50 and your router/switch.
  - Check the machine menu: `Comm.` ➔ `Ethernet` ➔ verify IP address matches `DEVICE_IP` in `.env`.

### 2. Error: `ERP API credentials rejected (401/403)`
- **Cause**: `ERP_API_TOKEN` in `.env` is incorrect or expired.
- **Solution**: Check the device token in Next Gen Service portal under Biometric Devices and update `.env`.

### 3. Machine IP Changes:
- If your router assigns a new IP to the K50, open `.env`, update `DEVICE_IP=...`, and restart the service or `start_auto_sync.bat`.

### 4. Viewing Log Files:
- Live Agent Logs: `C:\laragon\www\school\python\logs\agent.log`
- Service Startup Logs: `C:\laragon\www\school\python\logs\service_startup.log`
