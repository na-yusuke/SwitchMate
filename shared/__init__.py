# Utilities Library

from . import hmac
from .connect_wifi import connect_wifi
from .logger import LogLevel, configure, get_logger
from .system import reboot, safe_reboot

__version__ = "1.0.0"
__all__ = [
    # Connect WiFi
    "connect_wifi",
    # HMAC
    "hmac",
    # Logger
    "LogLevel",
    "configure",
    "get_logger",
    # System
    "reboot",
    "safe_reboot",
]
