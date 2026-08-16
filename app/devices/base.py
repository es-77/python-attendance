from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BiometricDeviceException(Exception):
    """Base exception for biometric device operations."""
    pass

class BiometricDevice(ABC):
    """Abstract base class representing a biometric hardware device."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection with the physical device."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection with the physical device."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is currently active."""
        pass

    @abstractmethod
    def get_device_information(self) -> Dict[str, Any]:
        """Retrieve hardware/firmware metadata."""
        pass

    @abstractmethod
    def get_attendance(self) -> List[Dict[str, Any]]:
        """Retrieve list of attendance records (READ-ONLY)."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test physical connection and return status."""
        pass

    @abstractmethod
    def get_users(self) -> List[Dict[str, Any]]:
        """Retrieve list of users registered on the device."""
        pass

    @abstractmethod
    def write_user(self, user_id: str, name: str) -> bool:
        """Write/update a user profile on the physical device."""
        pass
