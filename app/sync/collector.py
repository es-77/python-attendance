import logging
from typing import Dict, Any

from app.devices.base import BiometricDevice
from app.sync.queue import LocalQueue

logger = logging.getLogger('collector')

class AttendanceCollector:
    """Orchestrates reading records from the biometric device and pushing them to the local database queue."""

    def __init__(self, device: BiometricDevice, queue: LocalQueue):
        self.device = device
        self.queue = queue

    def collect(self) -> Dict[str, Any]:
        """Fetch attendance from physical device and save new records to local database queue."""
        stats = {
            "total_read": 0,
            "new_inserted": 0,
            "duplicates_skipped": 0,
            "success": False,
            "error": None
        }

        try:
            # 1. Connect to device
            if not self.device.is_connected():
                self.device.connect()

            # 2. Fetch raw records (READ-ONLY)
            records = self.device.get_attendance()
            stats["total_read"] = len(records)

            # 3. Store new records locally
            for record in records:
                inserted = self.queue.enqueue_record(record)
                if inserted:
                    stats["new_inserted"] += 1
                else:
                    stats["duplicates_skipped"] += 1

            stats["success"] = True
            logger.info(
                f"Collection cycle complete. Read: {stats['total_read']} | "
                f"New: {stats['new_inserted']} | Duplicates: {stats['duplicates_skipped']}"
            )

        except Exception as e:
            stats["error"] = str(e)
            logger.error(f"Error during collection cycle: {str(e)}")
            
        finally:
            # Close connection to release socket resources
            try:
                self.device.disconnect()
            except Exception:
                pass

        return stats
