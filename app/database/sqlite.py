import sqlite3
import logging
import hashlib
from typing import List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger('database')

class SQLiteDB:
    """Manages the local SQLite database for queue and offline-first persistence."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self):
        """Get a raw sqlite3 connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        """Create database tables if they do not exist."""
        logger.info(f"Initializing SQLite database at: {self.db_path}")
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Create sync_records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    biometric_user_id TEXT NOT NULL,
                    punch_time TEXT NOT NULL,
                    status INTEGER NOT NULL,
                    punch_type INTEGER NOT NULL,
                    record_hash TEXT NOT NULL UNIQUE,
                    raw_data TEXT,
                    sync_status TEXT DEFAULT 'pending', -- 'pending', 'synced', 'failed'
                    server_id TEXT,
                    created_at TEXT NOT NULL,
                    synced_at TEXT,
                    last_error TEXT
                )
            """)
            
            # Index on sync_status and record_hash
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_records (sync_status)")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_record_hash ON sync_records (record_hash)")
            
            conn.commit()
        finally:
            conn.close()
        logger.info("SQLite database tables verified successfully.")

    @staticmethod
    def calculate_hash(device_id: str, biometric_user_id: str, punch_time: str, status: int, punch_type: int) -> str:
        """Calculate deterministic unique SHA-256 hash for a record."""
        raw_string = f"{device_id}{biometric_user_id}{punch_time}{status}{punch_type}"
        return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

    def has_record(self, record_hash: str) -> bool:
        """Check if record with this hash already exists in SQLite."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM sync_records WHERE record_hash = ?", (record_hash,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def add_record(self, record: Dict[str, Any], record_hash: str) -> bool:
        """Insert a normalized device record into local database as pending."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_records 
                (device_id, biometric_user_id, punch_time, status, punch_type, record_hash, raw_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['device_id'],
                record['biometric_user_id'],
                record['punch_time'],
                record['status'],
                record['punch_type'],
                record_hash,
                record.get('raw_data', ''),
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Hash already exists, silent ignore/duplicate
            return False
        except Exception as e:
            logger.error(f"Error adding record to SQLite: {str(e)}")
            raise
        finally:
            conn.close()

    def get_pending_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve a list of unsynced records."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sync_records WHERE sync_status != 'synced' ORDER BY id ASC LIMIT ?", 
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def mark_as_synced(self, record_hash: str, server_id: str = None) -> None:
        """Update record status to 'synced'."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sync_records 
                SET sync_status = 'synced', 
                    server_id = ?, 
                    synced_at = ?,
                    last_error = NULL
                WHERE record_hash = ?
            """, (server_id, datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), record_hash))
            conn.commit()
        finally:
            conn.close()

    def update_error(self, record_hash: str, error_msg: str) -> None:
        """Set sync status to 'failed' and record the error."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sync_records 
                SET sync_status = 'failed', 
                    last_error = ?
                WHERE record_hash = ?
            """, (error_msg, record_hash))
            conn.commit()
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        """Fetch statistics about database records."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(1) FROM sync_records WHERE sync_status = 'pending'")
            pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(1) FROM sync_records WHERE sync_status = 'synced'")
            synced = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(1) FROM sync_records WHERE sync_status = 'failed'")
            failed = cursor.fetchone()[0]
            
            cursor.execute("SELECT max(synced_at) FROM sync_records WHERE sync_status = 'synced'")
            last_sync = cursor.fetchone()[0]

            return {
                "pending": pending,
                "synced": synced,
                "failed": failed,
                "last_sync": last_sync
            }
        finally:
            conn.close()
