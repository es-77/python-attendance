import logging
from typing import List, Dict, Any
from app.database.sqlite import SQLiteDB

logger = logging.getLogger('queue')

class LocalQueue:
    """Helper wrapper for SQLite database queue management."""

    def __init__(self, db: SQLiteDB):
        self.db = db

    def enqueue_record(self, record: Dict[str, Any]) -> bool:
        """Calculate record hash and push it to the database queue if not present."""
        record_hash = self.db.calculate_hash(
            device_id=record['device_id'],
            biometric_user_id=record['biometric_user_id'],
            punch_time=record['punch_time'],
            status=record['status'],
            punch_type=record['punch_type']
        )
        
        # Check if already stored locally
        if self.db.has_record(record_hash):
            return False

        # Add to local sqlite queue
        return self.db.add_record(record, record_hash)

    def get_pending(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve pending queue items."""
        return self.db.get_pending_records(limit)

    def mark_synced(self, record_hash: str, server_id: str = None) -> None:
        """Mark record as successfully uploaded."""
        self.db.mark_as_synced(record_hash, server_id)

    def mark_failed(self, record_hash: str, error_msg: str) -> None:
        """Mark record sync error status."""
        self.db.update_error(record_hash, error_msg)

    def get_stats(self) -> Dict[str, int]:
        """Fetch local queue database statistics."""
        return self.db.get_stats()
