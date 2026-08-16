import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger('api_client')

class APIClientException(Exception):
    """Base exception for API client errors."""
    pass

class APIAuthenticationError(APIClientException):
    """Raised when authentication (API token) fails."""
    pass

class APIConnectionError(APIClientException):
    """Raised when the server is offline or unreachable."""
    pass

class APIClient:
    """Handles HTTPS communication with the Laravel ERP backend."""

    def __init__(self, api_url: str, token: str, device_name: str, timeout: int = 15):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.device_name = device_name
        self.timeout = timeout

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def test_api_connection(self) -> bool:
        """Ping the ERP server to test token authorization and network reachability."""
        try:
            # We can test with a simple heartbeat check
            return self.send_heartbeat(status="online")
        except APIAuthenticationError:
            logger.error("Authentication failed: Invalid ERP_API_TOKEN configuration.")
            raise
        except Exception as e:
            logger.error(f"API Connection test failed: {str(e)}")
            return False

    def send_attendance(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send a batch of normalized attendance records to the Laravel endpoint."""
        url = f"{self.api_url}/biometric/attendance/sync"
        payload = {
            "device_id": self.device_name,
            "records": records
        }

        try:
            logger.info(f"Sending {len(records)} records to ERP API: {url}...")
            response = requests.post(url, json=payload, headers=self.headers, timeout=self.timeout)
            
            if response.status_code in (401, 403):
                raise APIAuthenticationError("ERP API credentials rejected (401/403).")
                
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"ERP API sync response: {result.get('message', 'SUCCESS')}")
            return result

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred while syncing records: {str(e)}")
            raise APIClientException(f"ERP returned error status: {e.response.status_code}") from e
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error: ERP server is offline or unreachable: {str(e)}")
            raise APIConnectionError("ERP server unreachable. Storing logs locally.") from e
        except requests.exceptions.Timeout as e:
            logger.warning(f"Request timeout while syncing logs: {str(e)}")
            raise APIConnectionError("ERP server request timed out.") from e
        except Exception as e:
            logger.error(f"Unexpected error in API Client sync: {str(e)}")
            raise APIClientException(f"Unexpected error: {str(e)}") from e

    def send_heartbeat(self, status: str = "online") -> bool:
        """Send device status heartbeat to the ERP backend."""
        url = f"{self.api_url}/biometric/device/heartbeat"
        payload = {
            "device_id": self.device_name,
            "device_name": self.device_name,
            "agent_version": "1.0.0",
            "device_status": status
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=self.timeout)
            logger.info(f"Heartbeat Response Status: {response.status_code}")
            logger.info(f"Heartbeat Response Content: {response.text}")
            
            if response.status_code in (401, 403):
                raise APIAuthenticationError(f"ERP API credentials rejected on heartbeat: {response.text}")
                
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Heartbeat failed: {type(e).__name__} - {str(e)}")
            if isinstance(e, APIAuthenticationError):
                raise
            return False

    def get_mapped_users(self) -> List[Dict[str, Any]]:
        """Fetch the list of mapped users from the ERP backend."""
        url = f"{self.api_url}/biometric/device/users"
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code in (401, 403):
                raise APIAuthenticationError(f"ERP API credentials rejected on get_mapped_users: {response.text}")
            response.raise_for_status()
            return response.json().get('users', [])
        except Exception as e:
            logger.error(f"Failed to fetch mapped users: {type(e).__name__} - {str(e)}")
            if isinstance(e, APIAuthenticationError):
                raise
            return []
