import os
import tempfile
import pytest
from datetime import datetime

from app.config import Config, ConfigError
from app.database.sqlite import SQLiteDB
from app.sync.queue import LocalQueue
from app.devices.base import BiometricDevice
from app.sync.collector import AttendanceCollector

class MockBiometricDevice(BiometricDevice):
    """Mocks the biometric device for testing without physical hardware."""
    
    def __init__(self, name="MockK50"):
        self.name = name
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_device_information(self):
        return {
            "name": "Mock K50",
            "serial_number": "MOCK12345678",
            "firmware_version": "V1.0.0",
            "platform": "MOCK_PLATFORM"
        }

    def get_attendance(self):
        return [
            {
                "device_id": self.name,
                "biometric_user_id": "1001",
                "punch_time": "2026-08-14T08:15:23",
                "status": 1,
                "punch_type": 0,
                "raw_data": "Mock raw data"
            },
            {
                "device_id": self.name,
                "biometric_user_id": "1002",
                "punch_time": "2026-08-14T08:16:45",
                "status": 1,
                "punch_type": 0,
                "raw_data": "Mock raw data 2"
            }
        ]

    def test_connection(self) -> bool:
        return True


def test_config_validation():
    """Test configuration validation rules."""
    # Temporarily modify configuration
    orig_ip = Config.DEVICE_IP
    
    Config.DEVICE_IP = None
    with pytest.raises(ConfigError):
        Config.validate()
        
    Config.DEVICE_IP = orig_ip


def test_record_hash_generation():
    """Test SHA-256 hash generation is deterministic and unique."""
    hash1 = SQLiteDB.calculate_hash("K50-MAIN", "1001", "2026-08-14T08:15:23", 1, 0)
    hash2 = SQLiteDB.calculate_hash("K50-MAIN", "1001", "2026-08-14T08:15:23", 1, 0)
    hash3 = SQLiteDB.calculate_hash("K50-MAIN", "1002", "2026-08-14T08:15:23", 1, 0)
    
    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64


def test_sqlite_queue_and_duplicates():
    """Test SQLite database operations and duplicate detection."""
    # Use temporary file for sqlite database
    fd, temp_db_path = tempfile.mkstemp()
    os.close(fd)
    
    try:
        db = SQLiteDB(temp_db_path)
        db.initialize()
        queue = LocalQueue(db)
        
        record = {
            "device_id": "K50-MAIN",
            "biometric_user_id": "1001",
            "punch_time": "2026-08-14T08:15:23",
            "status": 1,
            "punch_type": 0,
            "raw_data": "UID: 1, User: 1001"
        }
        
        # Test inserting record
        inserted = queue.enqueue_record(record)
        assert inserted is True
        
        # Test inserting duplicate record (should be ignored and return False)
        duplicate_inserted = queue.enqueue_record(record)
        assert duplicate_inserted is False
        
        # Test status counts
        stats = queue.get_stats()
        assert stats['pending'] == 1
        assert stats['synced'] == 0
        
        # Test get pending
        pending = queue.get_pending()
        assert len(pending) == 1
        assert pending[0]['biometric_user_id'] == '1001'
        
        # Test marking synced
        record_hash = db.calculate_hash(
            record['device_id'], 
            record['biometric_user_id'], 
            record['punch_time'], 
            record['status'], 
            record['punch_type']
        )
        queue.mark_synced(record_hash, server_id="42")
        
        # Verify updated counts
        stats = queue.get_stats()
        assert stats['pending'] == 0
        assert stats['synced'] == 1
        
    finally:
        # Delete temp file
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)


def test_collector_cycle():
    """Test collector fetches records from device and adds to queue."""
    fd, temp_db_path = tempfile.mkstemp()
    os.close(fd)
    
    try:
        db = SQLiteDB(temp_db_path)
        db.initialize()
        queue = LocalQueue(db)
        
        device = MockBiometricDevice(name="MockK50")
        collector = AttendanceCollector(device, queue)
        
        # Collect logs
        stats = collector.collect()
        
        assert stats['success'] is True
        assert stats['total_read'] == 2
        assert stats['new_inserted'] == 2
        assert stats['duplicates_skipped'] == 0
        
        # Check SQLite contains records
        db_stats = queue.get_stats()
        assert db_stats['pending'] == 2
        
    finally:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
