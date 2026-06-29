import logging
import sys
import os
from typing import Optional

def setup_logging(name: Optional[str] = "community_hero") -> logging.Logger:
    """
    Sets up a unified logging configuration for the project.
    Respects DEBUG environment variable for log level.
    """
    logger = logging.getLogger(name)
    
    # Only configure if it hasn't been configured yet
    if not logger.handlers:
        # Set log level based on DEBUG environment variable
        debug_mode = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
        log_level = logging.DEBUG if debug_mode else logging.INFO
        logger.setLevel(log_level)
        
        # Format for logs: Timestamp | Level | Name | Message
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        if debug_mode:
            logger.info("DEBUG mode enabled - verbose logging active")
        
        # File handler - save logs to app.log
        try:
            file_handler = logging.FileHandler("app.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.info("File logging enabled: app.log")
        except Exception as e:
            logger.warning(f"Could not enable file logging: {e}")

    return logger

# Create a default logger instance
logger = setup_logging()
