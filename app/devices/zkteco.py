import time
import logging
from typing import List, Dict, Any
from zk import ZK
from zk.exception import ZKError

from app.devices.base import BiometricDevice, BiometricDeviceException

logger = logging.getLogger('zkteco')

class ZKTecoK50Device(BiometricDevice):
    """Implementation of ZKTeco K50 device communication using pyzk."""

    def __init__(self, name: str, ip: str, port: int = 4370, timeout: int = 10):
        self.name = name
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self._zk = None
        self._conn = None

    def connect(self) -> bool:
        """Establish connection with exponential backoff retries."""
        if self.is_connected():
            return True

        self._zk = ZK(
            self.ip,
            port=self.port,
            timeout=self.timeout,
            password=0,
            force_udp=False,
            ommit_ping=False
        )

        retries = [5, 10, 30]
        attempt = 0

        while True:
            try:
                logger.info(f"Connecting to K50 device at {self.ip}:{self.port} (Attempt {attempt + 1})...")
                self._conn = self._zk.connect()
                logger.info("Successfully connected to ZKTeco K50 device.")
                return True
            except Exception as e:
                logger.warning(f"Connection failed: {type(e).__name__} - {str(e)}")
                if attempt < len(retries):
                    sleep_time = retries[attempt]
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    attempt += 1
                else:
                    logger.error("Failed to connect after all retries.")
                    raise BiometricDeviceException(f"Could not connect to K50 device: {str(e)}") from e

    def disconnect(self) -> None:
        """Disconnect from the physical device safely."""
        if self._conn:
            try:
                self._conn.disconnect()
                logger.info("Disconnected from K50 device.")
            except Exception as e:
                logger.warning(f"Error while disconnecting: {str(e)}")
            finally:
                self._conn = None
                self._zk = None

    def is_connected(self) -> bool:
        """Check if connection is alive."""
        # pyzk doesn't have a reliable connection check; we check if _conn is set.
        return self._conn is not None

    def get_device_information(self) -> Dict[str, Any]:
        """Read device system metadata safely."""
        self._ensure_connected()
        try:
            # READ-ONLY calls only
            device_name = self._conn.get_device_name()
            serial = self._conn.get_serialnumber()
            firmware = self._conn.get_firmware_version()
            platform = self._conn.get_platform()
            
            return {
                "name": device_name,
                "serial_number": serial,
                "firmware_version": firmware,
                "platform": platform
            }
        except Exception as e:
            logger.error(f"Failed to read device info: {str(e)}")
            raise BiometricDeviceException(f"Error reading device info: {str(e)}") from e

    def get_attendance(self) -> List[Dict[str, Any]]:
        """Read attendance records from the device and normalize them."""
        self._ensure_connected()
        try:
            logger.info("Fetching attendance logs from K50 device...")
            # READ-ONLY pyzk get_attendance()
            raw_records = self._conn.get_attendance()
            logger.info(f"Retrieved {len(raw_records)} raw records from K50.")

            normalized_records = []
            for record in raw_records:
                # Format timestamp in ISO-8601 format: YYYY-MM-DDTHH:MM:SS
                timestamp_str = record.timestamp.strftime('%Y-%m-%dT%H:%M:%S')
                
                normalized = {
                    "device_id": self.name,
                    "biometric_user_id": str(record.user_id),
                    "punch_time": timestamp_str,
                    "status": int(record.status),
                    "punch_type": int(record.punch),
                    "raw_data": f"UID: {record.uid}, User: {record.user_id}, Time: {record.timestamp}, Status: {record.status}, Punch: {record.punch}"
                }
                normalized_records.append(normalized)

            return normalized_records
        except Exception as e:
            logger.error(f"Failed to read attendance logs: {str(e)}")
            raise BiometricDeviceException(f"Error fetching attendance: {str(e)}") from e

    def test_connection(self) -> bool:
        """Quick ping/connect check."""
        try:
            zk = ZK(self.ip, port=self.port, timeout=5)
            conn = zk.connect()
            conn.disconnect()
            return True
        except Exception:
            return False

    def get_users(self) -> List[Dict[str, Any]]:
        """Read users registered on the physical device."""
        self._ensure_connected()
        try:
            raw_users = self._conn.get_users()
            users = []
            for u in raw_users:
                users.append({
                    "uid": u.uid,
                    "device_user_id": str(u.user_id),
                    "name": u.name,
                    "privilege": u.privilege,
                })
            return users
        except Exception as e:
            logger.error(f"Failed to read users from device: {str(e)}")
            raise BiometricDeviceException(f"Error reading users from device: {str(e)}") from e

    def write_user(self, user_id: str, name: str) -> bool:
        """Write/update a user profile on the physical device using pyzk."""
        self._ensure_connected()
        try:
            logger.info(f"Writing user profile to K50 device: ID={user_id}, Name={name}")
            uid = int(user_id)
            self._conn.set_user(
                uid=uid,
                name=name,
                privilege=0,
                password='',
                group_id=1,
                user_id=user_id
            )
            return True
        except Exception as e:
            logger.error(f"Failed to write user to K50 device: {str(e)}")
            raise BiometricDeviceException(f"Error writing user to device: {str(e)}") from e

    def _ensure_connected(self):
        if not self.is_connected():
            raise BiometricDeviceException("Device is not connected. Call connect() first.")
