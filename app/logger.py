import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(log_level='INFO'):
    """Configure rotating file logging and console logging."""
    # Ensure logs directory exists
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'agent.log')
    
    # Map string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Formatter definition
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid double logging
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # 1. Rotating File Handler (max 5MB, keeping 3 backups)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)
    root_logger.addHandler(file_handler)

    # 2. Console Handler (Standard Output)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    root_logger.addHandler(console_handler)

    logging.info(f"Logger initialized successfully. Logs written to {log_file}")
