# ZKTeco K50 Biometric Attendance Sync Agent

A production-ready Windows Biometric Sync Agent written in Python 3. It communicates with a physical ZKTeco K50 biometric machine over TCP/IP (port 4370) and synchronizes attendance logs with the Laravel ERP backend over secure HTTPS.

---

## Architecture
```
  [ ZKTeco K50 Device ] (192.168.1.201)
           │
           ▼ TCP/IP Port :4370
  [ Windows Biometric Agent ] (Local PC Running SQLite Sync Queue)
           │
           ▼ HTTPS POST
  [ Laravel ERP Backend ] (Hetzner VPS / Local Laragon Server)
```

---

## Core Features
1. **Offline-First Resilience**: If the internet is disconnected or the Laravel server goes offline, logs are safely cached in the local SQLite queue (`biometric_agent.db`). They will be synced automatically once connection is restored.
2. **Read-Only Safeties**: The agent never performs destructive actions on the biometric device (no user edits, rebooting, or log-clearing).
3. **Double-Sync Protection**: Computes deterministic SHA-256 hashes of punches to prevent duplicate uploads.
4. **Resiliency**: Exponential backoff reconnection loop when the ZKTeco K50 becomes temporarily offline.
5. **Windows Service Support**: Can run silently in the background on startup.

---

## 1. Setup Instructions

### Prerequisites
- Python 3.8+ (Python 3.12 recommended)
- Administrator privilege (for Windows Service installation only)

### Installation
1. Open Windows Command Prompt or Laragon terminal and navigate to the python agent directory:
   ```cmd
   cd C:\laragon\www\school\python
   ```

2. Create and activate a Python virtual environment:
   ```cmd
   py -m venv .venv
   .venv\Scripts\activate
   ```

3. Install required packages:
   ```cmd
   pip install -r requirements.txt
   ```

---

## 2. Configuration
Copy the `.env.example` file to `.env`:
```cmd
copy .env.example .env
```
Open `.env` and adjust settings:
```ini
DEVICE_NAME=K50-MAIN
DEVICE_IP=192.168.1.201
DEVICE_PORT=4370
DEVICE_TIMEOUT=10

# For Laragon local test:
ERP_API_URL=http://localhost:8000/api/v1/emmanuel
ERP_API_TOKEN=test-token-k50

# Synchronization interval (seconds)
SYNC_INTERVAL=60
LOCAL_DATABASE=biometric_agent.db
LOG_LEVEL=INFO
```

---

## 3. CLI Run Options

### Run Diagnostics test
Tests config, SQLite, network ports, K50 communication, and remote Laravel API authentication:
```cmd
python main.py --test
```

### Print Hardware Information
Query device name, serial number, firmware, and platform:
```cmd
python main.py --device-info
```

### Run One-Time Synchronization
Read K50 logs, queue them locally, upload unsynced records, send heartbeat, and exit:
```cmd
python main.py --sync-once
```

### Print SQLite Queue Status
Shows pending, synced, and failed counts:
```cmd
python main.py --status
```

### Continuous Loop Background Mode
Default operation. Runs continuously:
```cmd
python main.py
```

---

## 4. Run Automated Unit Tests
A comprehensive test suite using mock biometric devices is included. Run it with:
```cmd
python -m pytest
```

---

## 5. Windows Background Service Setup

### Automatic Installation
Run this inside an **Administrator Command Prompt**:
```cmd
python install_service.py
```
To start the background service:
```cmd
net start BiometricSyncAgent
```

### Uninstallation
```cmd
python uninstall_service.py
```

### Manual Alternative (NSSM)
If you encounter `pywin32` permission locks, you can use the Non-Sucking Service Manager (NSSM):
1. Download NSSM from [nssm.cc](https://nssm.cc/).
2. Run `nssm install BiometricSyncAgent`.
3. Select `python.exe` as path, and `C:\laragon\www\school\python\main.py` as argument.
4. Set Startup Type to Automatic.

---

## 6. Troubleshooting

- **ZKTeco K50 Offline**:
  - Verify network connection using ping: `ping 192.168.1.201`
  - Ensure the timeout variable in `.env` is high enough (e.g. 10-15 seconds).
- **ERP API Token Rejected (401/403)**:
  - Verify `ERP_API_TOKEN` matches the `api_token` generated on the Laravel `biometric_devices` record.
  - Verify that the tenant's subscription/trial plan is not expired.
- **SQLite Database Locked**:
  - Ensure there is only one instance of the agent running.
- **Log Files**:
  - Inspect `logs/agent.log` for detailed warning/error stack traces.
