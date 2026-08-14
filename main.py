import sys
import argparse
import time
import socket
import logging
from datetime import datetime

from app.config import Config, ConfigError
from app.logger import setup_logger
from app.devices.zkteco import ZKTecoK50Device
from app.database.sqlite import SQLiteDB
from app.sync.queue import LocalQueue
from app.sync.collector import AttendanceCollector
from app.sync.synchronizer import AttendanceSynchronizer
from app.api.client import APIClient

def run_test():
    """Runs system diagnostics checks."""
    print("=" * 60)
    print("BIOMETRIC SYNC AGENT DIAGNOSTICS")
    print("=" * 60)

    # 1. Configuration
    try:
        Config.validate()
        print("[OK] Configuration loaded and validated successfully.")
    except ConfigError as e:
        print(f"[FAIL] Configuration error:\n{str(e)}")
        sys.exit(1)

    # 2. Database Initialization
    try:
        db = SQLiteDB(Config.LOCAL_DATABASE)
        db.initialize()
        queue = LocalQueue(db)
        print(f"[OK] Local SQLite database verified at {Config.LOCAL_DATABASE}")
    except Exception as e:
        print(f"[FAIL] Database initialization failed: {str(e)}")
        sys.exit(1)

    # 3. Network Check to K50
    try:
        with socket.create_connection((Config.DEVICE_IP, Config.DEVICE_PORT), timeout=5):
            print(f"[OK] Network reachable: Port {Config.DEVICE_PORT} is open on {Config.DEVICE_IP}")
    except Exception as e:
        print(f"[FAIL] Network check to ZKTeco K50 failed: {str(e)}")
        sys.exit(1)

    # 4. K50 Device Connection
    device = ZKTecoK50Device(
        name=Config.DEVICE_NAME,
        ip=Config.DEVICE_IP,
        port=Config.DEVICE_PORT,
        timeout=Config.DEVICE_TIMEOUT
    )
    
    try:
        device.connect()
        print("[OK] ZKTeco K50 connection established successfully.")
    except Exception as e:
        print(f"[FAIL] Connection to K50 failed: {str(e)}")
        sys.exit(1)

    # 5. Get Device Info
    try:
        info = device.get_device_information()
        print("[OK] Device information retrieved successfully:")
        print(f"  - Serial Number: {info['serial_number']}")
        print(f"  - Model/Name: {info['name']}")
        print(f"  - Firmware: {info['firmware_version']}")
        print(f"  - Platform: {info['platform']}")
    except Exception as e:
        print(f"[FAIL] Failed to read device information: {str(e)}")
        device.disconnect()
        sys.exit(1)

    # 6. Read Attendance Records
    try:
        records = device.get_attendance()
        print(f"[OK] Attendance records read: {len(records)} records retrieved.")
    except Exception as e:
        print(f"[FAIL] Failed to read attendance logs: {str(e)}")
        device.disconnect()
        sys.exit(1)
    finally:
        device.disconnect()

    # 7. Laravel API Client & Authentication
    api_client = APIClient(
        api_url=Config.ERP_API_URL,
        token=Config.ERP_API_TOKEN,
        device_name=Config.DEVICE_NAME,
        timeout=10
    )
    
    try:
        reachable = api_client.test_api_connection()
        if reachable:
            print("[OK] Laravel ERP API connection and Bearer Token validated.")
        else:
            print("[FAIL] Laravel ERP API heartbeat test returned failure status.")
            sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Laravel ERP API authentication failed: {str(e)}")
        sys.exit(1)

    print("-" * 60)
    print("DIAGNOSTICS PASSED: Biometric Sync Agent is production-ready!")
    print("=" * 60)

def show_device_info():
    """Reads K50 information and prints it."""
    try:
        Config.validate()
    except ConfigError as e:
        print(f"Configuration error: {str(e)}")
        sys.exit(1)

    device = ZKTecoK50Device(Config.DEVICE_NAME, Config.DEVICE_IP, Config.DEVICE_PORT, Config.DEVICE_TIMEOUT)
    try:
        device.connect()
        info = device.get_device_information()
        print("=" * 40)
        print("ZKTeco K50 Hardware Information")
        print("=" * 40)
        print(f"Device Name: {info['name']}")
        print(f"Serial Number: {info['serial_number']}")
        print(f"Firmware: {info['firmware_version']}")
        print(f"Platform: {info['platform']}")
        print("=" * 40)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        device.disconnect()

def show_status():
    """Prints local database status statistics."""
    try:
        Config.validate()
    except ConfigError as e:
        print(f"Configuration error: {str(e)}")
        sys.exit(1)

    db = SQLiteDB(Config.LOCAL_DATABASE)
    db.initialize()
    stats = db.get_stats()
    
    print("=" * 40)
    print("Local Database Sync Queue Status")
    print("=" * 40)
    print(f"Pending Sync: {stats['pending']}")
    print(f"Synced:       {stats['synced']}")
    print(f"Failed:       {stats['failed']}")
    print(f"Last Sync:    {stats['last_sync'] or 'Never'}")
    print("=" * 40)

def run_sync_once(dry_run=False):
    """Executes exactly one sync cycle."""
    try:
        Config.validate()
    except ConfigError as e:
        print(f"Configuration error: {str(e)}")
        sys.exit(1)

    setup_logger(Config.LOG_LEVEL)
    logging.info("Starting one-time synchronization cycle...")

    db = SQLiteDB(Config.LOCAL_DATABASE)
    db.initialize()
    queue = LocalQueue(db)

    # 1. Collector (Read K50 -> Save SQLite)
    device = ZKTecoK50Device(Config.DEVICE_NAME, Config.DEVICE_IP, Config.DEVICE_PORT, Config.DEVICE_TIMEOUT)
    collector = AttendanceCollector(device, queue)
    collect_stats = collector.collect()

    # 2. Synchronizer (SQLite -> Send API)
    api_client = APIClient(Config.ERP_API_URL, Config.ERP_API_TOKEN, Config.DEVICE_NAME, Config.DEVICE_TIMEOUT)
    synchronizer = AttendanceSynchronizer(api_client, queue)
    
    if not dry_run:
        sync_stats = synchronizer.synchronize()
        synchronizer.heartbeat(status="online")
        
        logging.info("One-time synchronization finished.")
        return collect_stats, sync_stats
    else:
        logging.info("One-time synchronization finished (DRY RUN - server post skipped).")
        return collect_stats, None

def run_agent_loop():
    """Runs the background agent loop continuously."""
    try:
        Config.validate()
    except ConfigError as e:
        print(f"Configuration error: {str(e)}")
        sys.exit(1)

    setup_logger(Config.LOG_LEVEL)
    logging.info("Starting Biometric Sync Agent loop...")

    db = SQLiteDB(Config.LOCAL_DATABASE)
    db.initialize()
    queue = LocalQueue(db)

    device = ZKTecoK50Device(Config.DEVICE_NAME, Config.DEVICE_IP, Config.DEVICE_PORT, Config.DEVICE_TIMEOUT)
    collector = AttendanceCollector(device, queue)

    api_client = APIClient(Config.ERP_API_URL, Config.ERP_API_TOKEN, Config.DEVICE_NAME, Config.DEVICE_TIMEOUT)
    synchronizer = AttendanceSynchronizer(api_client, queue)

    # Send initial heartbeat
    synchronizer.heartbeat(status="online")

    try:
        while True:
            logging.info("Starting sync cycle...")
            
            # Read from device
            collector.collect()
            
            # Sync to ERP
            synchronizer.synchronize()
            
            # Heartbeat update
            synchronizer.heartbeat(status="online")
            
            logging.info(f"Sync cycle finished. Sleeping for {Config.SYNC_INTERVAL} seconds.")
            time.sleep(Config.SYNC_INTERVAL)
            
    except KeyboardInterrupt:
        logging.info("Agent stopped manually by user (KeyboardInterrupt). Sending offline heartbeat...")
        synchronizer.heartbeat(status="offline")
    except Exception as e:
        logging.critical(f"Unhandled critical crash inside agent loop: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ZKTeco K50 Biometric Sync Agent")
    parser.add_argument('--test', action='store_true', help="Run configuration and connection diagnostic checks")
    parser.add_argument('--device-info', action='store_true', help="Read and print ZKTeco K50 device hardware metadata")
    parser.add_argument('--sync-once', action='store_true', help="Run exactly one read and synchronize cycle, then exit")
    parser.add_argument('--status', action='store_true', help="Show SQLite database sync queue status counts")
    parser.add_argument('--dry-run', action='store_true', help="With --sync-once, read records but do not upload to ERP")

    args = parser.parse_args()

    if args.test:
        run_test()
    elif args.device_info:
        show_device_info()
    elif args.status:
        show_status()
    elif args.sync_once:
        run_sync_once(args.dry_run)
    else:
        run_agent_loop()
