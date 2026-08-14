import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass

class Config:
    DEVICE_NAME = os.getenv('DEVICE_NAME', 'K50-MAIN')
    DEVICE_IP = os.getenv('DEVICE_IP')
    DEVICE_PORT = os.getenv('DEVICE_PORT')
    DEVICE_TIMEOUT = os.getenv('DEVICE_TIMEOUT', '10')

    ERP_API_URL = os.getenv('ERP_API_URL')
    ERP_API_TOKEN = os.getenv('ERP_API_TOKEN')

    SYNC_INTERVAL = os.getenv('SYNC_INTERVAL', '60')
    LOCAL_DATABASE = os.getenv('LOCAL_DATABASE', 'biometric_agent.db')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """Validate all required configurations are present and valid."""
        errors = []

        if not cls.DEVICE_IP:
            errors.append("DEVICE_IP is required but not specified in .env.")
        
        if not cls.DEVICE_PORT:
            errors.append("DEVICE_PORT is required but not specified in .env.")
        else:
            try:
                port = int(cls.DEVICE_PORT)
                if not (0 < port <= 65535):
                    errors.append(f"DEVICE_PORT must be a valid port number (0-65535), got '{cls.DEVICE_PORT}'.")
            except ValueError:
                errors.append(f"DEVICE_PORT must be an integer, got '{cls.DEVICE_PORT}'.")

        if not cls.DEVICE_TIMEOUT:
            errors.append("DEVICE_TIMEOUT must be specified in .env.")
        else:
            try:
                int(cls.DEVICE_TIMEOUT)
            except ValueError:
                errors.append(f"DEVICE_TIMEOUT must be an integer, got '{cls.DEVICE_TIMEOUT}'.")

        if not cls.ERP_API_URL:
            errors.append("ERP_API_URL is required but not specified in .env.")
        elif not cls.ERP_API_URL.startswith(('http://', 'https://')):
            errors.append("ERP_API_URL must start with http:// or https://")
        elif cls.ERP_API_URL.startswith('http://') and os.getenv('NODE_ENV') == 'production':
            # Block HTTP in production unless explicitly in dev mode
            errors.append("ERP_API_URL must use HTTPS in production environments.")

        if not cls.ERP_API_TOKEN:
            errors.append("ERP_API_TOKEN is required but not specified in .env.")

        if not cls.SYNC_INTERVAL:
            errors.append("SYNC_INTERVAL must be specified in .env.")
        else:
            try:
                int(cls.SYNC_INTERVAL)
            except ValueError:
                errors.append(f"SYNC_INTERVAL must be an integer, got '{cls.SYNC_INTERVAL}'.")

        if errors:
            raise ConfigError("\n".join(errors))

        # Convert numeric settings
        cls.DEVICE_PORT = int(cls.DEVICE_PORT)
        cls.DEVICE_TIMEOUT = int(cls.DEVICE_TIMEOUT)
        cls.SYNC_INTERVAL = int(cls.SYNC_INTERVAL)
