"""
Lightweight logging system for MicroPython
Power-efficient and memory-optimized logging system
"""

import time


class LogLevel:
    """Log level constants"""

    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    NONE = 5  # Completely disable logging


class Logger:
    """Lightweight logger class"""

    # Class variables (shared across all instances)
    _global_level = LogLevel.INFO
    _enabled = True
    _show_timestamp = True
    _show_level = True

    def __init__(self, name):
        """
        Initialize logger

        Args:
            name: Logger name (typically module name)
        """
        self.name = name

    @classmethod
    def set_level(cls, level):
        """
        Set global log level

        Args:
            level: LogLevel constant
        """
        cls._global_level = level

    @classmethod
    def enable(cls):
        """Enable logging"""
        cls._enabled = True

    @classmethod
    def disable(cls):
        """Disable logging (for power saving mode)"""
        cls._enabled = False

    @classmethod
    def set_timestamp(cls, enabled):
        """Toggle timestamp display"""
        cls._show_timestamp = enabled

    @classmethod
    def set_show_level(cls, enabled):
        """Toggle log level display"""
        cls._show_level = enabled

    def _log(self, level, level_name, message):
        """Internal log method"""
        if not self._enabled or level < self._global_level:
            return

        parts = []

        # Timestamp
        if self._show_timestamp:
            timestamp = time.ticks_ms()
            parts.append(f"[{timestamp:010d}]")

        # Log level
        if self._show_level:
            parts.append(f"[{level_name}]")

        # Logger name
        parts.append(f"[{self.name}]")

        # Message
        parts.append(message)

        print(" ".join(parts))

    def debug(self, message):
        """Log at DEBUG level"""
        self._log(LogLevel.DEBUG, "DEBUG", message)

    def info(self, message):
        """Log at INFO level"""
        self._log(LogLevel.INFO, "INFO", message)

    def warning(self, message):
        """Log at WARNING level"""
        self._log(LogLevel.WARNING, "WARN", message)

    def error(self, message):
        """Log at ERROR level"""
        self._log(LogLevel.ERROR, "ERROR", message)

    def critical(self, message):
        """Log at CRITICAL level"""
        self._log(LogLevel.CRITICAL, "CRIT", message)


# Helper functions for global configuration
def set_log_level(level):
    """Set global log level"""
    Logger.set_level(level)


def enable_logging():
    """Enable logging"""
    Logger.enable()


def disable_logging():
    """Disable logging (power saving mode)"""
    Logger.disable()


def configure(level=LogLevel.INFO, timestamp=True, show_level=True):
    """
    Configure logging system

    Args:
        level: Log level
        timestamp: Whether to show timestamp
        show_level: Whether to show log level
    """
    Logger.set_level(level)
    Logger.set_timestamp(timestamp)
    Logger.set_show_level(show_level)


# Factory function
def get_logger(name):
    """
    Get logger instance

    Args:
        name: Logger name (typically pass __name__)

    Returns:
        Logger: Logger instance
    """
    return Logger(name)
