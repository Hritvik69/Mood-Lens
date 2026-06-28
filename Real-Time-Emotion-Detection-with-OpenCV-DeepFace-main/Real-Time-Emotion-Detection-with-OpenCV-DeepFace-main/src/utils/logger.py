"""
Logger utility for consistent logging across the application
"""
import logging
import sys
from datetime import datetime

def setup_logger(name="EmotionAI", level=logging.INFO):
    """
    Sets up a logger with colored output
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger
