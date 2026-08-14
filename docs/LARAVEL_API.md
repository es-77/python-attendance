# Laravel ERP Biometric Integration API

This document details the HTTP API endpoints implemented on the Laravel ERP backend to receive synchronized data and heartbeats from the Windows Biometric Sync Agent.

## Base URL
All API requests must target the tenant-specific endpoint path:
`https://<YOUR-ERP-DOMAIN>.com/api/v1/<tenant-subdomain>/`

Local Laragon Testing URL:
`http://localhost:8000/api/v1/emmanuel/`

---

## Authentication
Authentication is enforced via custom Bearer tokens. Each biometric device registered on the ERP generates a unique token stored in the `api_token` column of the `biometric_devices` table.

Include the token in all HTTP headers:
```http
Authorization: Bearer <DEVICE_API_TOKEN>
Accept: application/json
Content-Type: application/json
```

---

## Endpoints

### 1. Attendance Log Synchronization
Pushes a batch of raw attendance records from the local SQLite queue to the ERP database.

* **URL**: `biometric/attendance/sync`
* **Method**: `POST`
* **Headers**: Requires Bearer authentication.
* **Payload**:
```json
{
    "device_id": "K50-MAIN",
    "records": [
        {
            "biometric_user_id": "1",
            "punch_time": "2026-08-14T08:15:23",
            "status": 1,
            "punch_type": 0,
            "record_hash": "a4d33458ef8a8cd7..."
        }
    ]
}
```

* **Success Response (200 OK)**:
```json
{
    "success": true,
    "accepted": 1,
    "duplicates": 0,
    "failed": 0,
    "records": [
        {
            "record_hash": "a4d33458ef8a8cd7...",
            "status": "accepted"
        }
    ]
}
```

* **Notes on Controller Processing**:
  - The controller compares each incoming `record_hash` against existing records in `biometric_attendance_logs`.
  - It also cross-references natural keys `(device_user_id, punch_time)` to capture legacy records.
  - Duplicates are skipped gracefully (`status: duplicate`) and record hashes are backfilled when missing.
  - Successfully synced records return `status: accepted`.

---

### 2. Device Heartbeat
Informs the ERP of the agent's connectivity status, version, and health.

* **URL**: `biometric/device/heartbeat`
* **Method**: `POST`
* **Headers**: Requires Bearer authentication.
* **Payload**:
```json
{
    "device_id": "K50-MAIN",
    "device_name": "K50-MAIN",
    "agent_version": "1.0.0",
    "device_status": "online"
}
```

* **Success Response (200 OK)**:
```json
{
    "success": true,
    "message": "Heartbeat received successfully"
}
```

* **Notes on Controller Processing**:
  - Upon receiving the heartbeat, the ERP updates the device's status (`online`/`offline`) and logs `last_connected_at` timestamps in `biometric_devices` table.
