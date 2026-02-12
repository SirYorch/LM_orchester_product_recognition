"""
Logging configuration for the Business Backend application.

Provides centralized logging setup with standard Python logging module.
Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] FunctionName - Message
"""

import logging
import sys
from datetime import datetime


class CustomFormatter(logging.Formatter):
    """Custom formatter for logs with function name and timestamp."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        func_name = record.funcName if record.funcName != "<module>" else "module"
        level_name = record.levelname
        message = record.getMessage()
        return f"[{timestamp}] [{level_name}] {func_name} - {message}"


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logging.basicConfig(level=level)

    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = CustomFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


def get_logger(name: str = "business_backend") -> logging.Logger:
    """
    Get logger instance for a module.

    Args:
        name: Logger name (usually module name)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
