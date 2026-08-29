import sys
import os
import logging
import time

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
except ImportError:
    win32serviceutil = None
    win32service = None

def synchronize_device_users(api_client, device):
    """Pulls mapped users from ERP and registers them on the physical biometric device if missing or name changed."""
    logging.info("Starting device users synchronization...")
    try:
        erp_users = api_client.get_mapped_users()
        if not erp_users:
            logging.info("No mapped users defined in ERP.")
            return
            
        logging.info(f"Retrieved {len(erp_users)} mapped users from ERP.")

        device.connect()
        try:
            device_users = device.get_users()
            device_users_map = {u["device_user_id"]: u for u in device_users}

            for erp_user in erp_users:
                u_id = str(erp_user["device_user_id"])
                if not u_id.isdigit():
                    logging.warning(f"Skipping non-numeric device_user_id: {u_id}")
                    continue
                erp_name = erp_user["name"]

                if u_id not in device_users_map or device_users_map[u_id]["name"] != erp_name:
                    logging.info(f"--> Writing/updating user on physical device: ID={u_id}, Name={erp_name}")
                    device.write_user(user_id=u_id, name=erp_name)
                    time.sleep(0.5)
                else:
                    logging.info(f"--> User ID={u_id} '{erp_name}' ALREADY EXISTS on physical device memory.")
                    
            logging.info("Device users synchronization complete.")
        finally:
            device.disconnect()
    except Exception as e:
        logging.error(f"Device users sync failed: {str(e)}")

if win32serviceutil:
    class BiometricSyncService(win32serviceutil.ServiceFramework):
        """Windows Service wrapper for ZKTeco Biometric Sync Agent."""
        
        _svc_name_ = "BiometricSyncAgent"
        _svc_display_name_ = "ZKTeco K50 Biometric Sync Agent"
        _svc_description_ = "Background service to sync ZKTeco K50 attendance logs to Next Gen Service School ERP"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.running = True

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            self.running = False

        def SvcDoRun(self):
            import traceback
            from datetime import datetime
            
            service_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(service_dir)
            
            if service_dir not in sys.path:
                sys.path.append(service_dir)
                
            log_dir = os.path.join(service_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            startup_log_path = os.path.join(log_dir, "service_startup.log")
            
            with open(startup_log_path, "a") as f:
                f.write(f"\n[{datetime.now().isoformat()}] Service initialization sequence started.\n")
                f.write(f"sys.path: {sys.path}\n")

            try:
                from app.config import Config
                from app.logger import setup_logger
                from app.database.sqlite import SQLiteDB
                from app.sync.queue import LocalQueue
                from app.devices.zkteco import ZKTecoK50Device
                from app.sync.collector import AttendanceCollector
                from app.api.client import APIClient
                from app.sync.synchronizer import AttendanceSynchronizer
                
                try:
                    Config.validate()
                except Exception as config_err:
                    with open(startup_log_path, "a") as f:
                        f.write(f"Config Validation Failed: {str(config_err)}\n")
                    if servicemanager:
                        servicemanager.LogErrorMsg(f"Config Validation Failed: {str(config_err)}")
                    return

                setup_logger(Config.LOG_LEVEL)
                logging.info("Biometric Sync Windows Service starting...")
                with open(startup_log_path, "a") as f:
                    f.write("Service core components loaded. Handover to loop.\n")
                
                db = SQLiteDB(Config.LOCAL_DATABASE)
                db.initialize()
                queue = LocalQueue(db)
                
                device = ZKTecoK50Device(Config.DEVICE_NAME, Config.DEVICE_IP, Config.DEVICE_PORT, Config.DEVICE_TIMEOUT)
                collector = AttendanceCollector(device, queue)
                
                api_client = APIClient(Config.ERP_API_URL, Config.ERP_API_TOKEN, Config.DEVICE_NAME, Config.DEVICE_TIMEOUT)
                synchronizer = AttendanceSynchronizer(api_client, queue)
                
                # Initial heartbeat and device users sync
                synchronizer.heartbeat(status="online")
                try:
                    synchronize_device_users(api_client, device)
                except Exception as user_err:
                    logging.error(f"Initial device users sync error: {str(user_err)}")

                last_user_sync = time.time()
                user_sync_interval = getattr(Config, 'USER_SYNC_INTERVAL', 120)
                
                while self.running:
                    try:
                        collector.collect()
                        synchronizer.synchronize()
                        synchronizer.heartbeat(status="online")

                        # Sync device users every USER_SYNC_INTERVAL seconds (default: 120s / 2 mins)
                        current_time = time.time()
                        if current_time - last_user_sync >= user_sync_interval:
                            synchronize_device_users(api_client, device)
                            last_user_sync = current_time
                    except Exception as e:
                        logging.error(f"Error in background sync cycle: {str(e)}")
                    
                    timeout_ms = int(Config.SYNC_INTERVAL) * 1000
                    rc = win32event.WaitForSingleObject(self.hWaitStop, timeout_ms)
                    if rc == win32event.WAIT_OBJECT_0:
                        break
                        
                logging.info("Biometric Sync Windows Service stopped.")
                try:
                    synchronizer.heartbeat(status="offline")
                except Exception:
                    pass
            except Exception as e:
                error_trace = traceback.format_exc()
                with open(startup_log_path, "a") as f:
                    f.write(f"CRITICAL startup crash: {str(e)}\n{error_trace}\n")
                if servicemanager:
                    servicemanager.LogErrorMsg(f"CRITICAL startup crash: {str(e)}\n{error_trace}")
else:
    class BiometricSyncService:
        pass
