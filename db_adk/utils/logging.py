"""
Logging utilities for DB-ADK.
"""

import logging
import sys
import os
from functools import lru_cache
from logging.handlers import RotatingFileHandler

# Default log directory
DEFAULT_LOG_DIR = os.path.join(os.path.expanduser("~"), ".db_adk", "logs")

# Ensure log directory exists
os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)

@lru_cache()
def get_logger(name):
    """Get a logger with the given name.
    
    Args:
        name (str): The name of the logger.
        
    Returns:
        logging.Logger: The logger instance.
    """
    logger = logging.getLogger(name)
    
    # Skip setup if logger already has handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create file handler
    log_file = os.path.join(DEFAULT_LOG_DIR, "db_adk.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
