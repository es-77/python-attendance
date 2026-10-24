import logging
from typing import Dict, Any

from app.api.client import APIClient, APIConnectionError, APIAuthenticationError
from app.sync.queue import LocalQueue

logger = logging.getLogger('synchronizer')

class AttendanceSynchronizer:
    """Manages uploading pending local queue logs to the Laravel ERP backend."""

    def __init__(self, api_client: APIClient, queue: LocalQueue):
        self.api_client = api_client
        self.queue = queue

    def synchronize(self) -> Dict[str, Any]:
        """Fetch pending records and post them in batches to the ERP API until queue is empty."""
        stats = {
            "pending_before": 0,
            "uploaded": 0,
            "failed": 0,
            "duplicates_server": 0,
            "success": True,
            "error": None
        }

        first_batch = True

        while True:
            # 1. Fetch pending records (batch of 200)
            pending = self.queue.get_pending(limit=200)
            if first_batch:
                # Count total pending at start
                conn = self.queue.db.get_connection()
                try:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(1) FROM sync_records WHERE sync_status != 'synced'")
                    stats["pending_before"] = c.fetchone()[0]
                finally:
                    conn.close()
                first_batch = False

            if not pending:
                if stats["uploaded"] == 0 and stats["failed"] == 0 and stats["duplicates_server"] == 0:
                    logger.info("No pending records to synchronize.")
                break

            # Prepare records for the API payload
            records_payload = []
            for p in pending:
                records_payload.append({
                    "biometric_user_id": p["biometric_user_id"],
                    "punch_time": p["punch_time"],
                    "status": p["status"],
                    "punch_type": p["punch_type"],
                    "record_hash": p["record_hash"]
                })

            try:
                # 2. Call Laravel API
                response = self.api_client.send_attendance(records_payload)
                
                # 3. Parse and update local SQLite state based on server response
                server_records = response.get('records', [])
                server_records_map = {r['record_hash']: r for r in server_records}

                for p in pending:
                    h = p["record_hash"]
                    server_status = server_records_map.get(h, {})
                    
                    status_name = server_status.get('status')
                    if status_name == 'accepted':
                        self.queue.mark_synced(h)
                        stats["uploaded"] += 1
                    elif status_name == 'duplicate':
                        self.queue.mark_synced(h) # Already on server, resolve as synced
                        stats["duplicates_server"] += 1
                    elif status_name == 'failed':
                        error_msg = server_status.get('error', 'Server rejected record')
                        self.queue.mark_failed(h, error_msg)
                        stats["failed"] += 1
                    else:
                        # Fallback if status is missing, assume success since request succeeded
                        self.queue.mark_synced(h)
                        stats["uploaded"] += 1

                logger.info(
                    f"Batch sync complete. Uploaded: {stats['uploaded']} | "
                    f"Duplicates: {stats['duplicates_server']} | Failed: {stats['failed']}"
                )

            except APIAuthenticationError as e:
                stats["error"] = f"Authentication Failed: {str(e)}"
                stats["success"] = False
                logger.error(f"Cannot sync logs: {stats['error']}")
                for p in pending:
                    self.queue.mark_failed(p["record_hash"], "401/403 Unauthorized Device Token")
                break
                
            except APIConnectionError as e:
                stats["error"] = f"Connection Failed: {str(e)}"
                stats["success"] = False
                logger.warning(f"Server unreachable, logs remain queued locally. Details: {str(e)}")
                # Leave records as pending in queue for next cycle
                break
                
            except Exception as e:
                stats["error"] = f"Unexpected error during sync: {str(e)}"
                stats["success"] = False
                logger.error(stats["error"])
                for p in pending:
                    self.queue.mark_failed(p["record_hash"], str(e))
                break

        return stats

    def heartbeat(self, status: str = "online") -> bool:
        """Send device heartbeat/status update to ERP backend."""
        try:
            return self.api_client.send_heartbeat(status=status)
        except Exception as e:
            logger.warning(f"Failed to send heartbeat: {str(e)}")
            return False
