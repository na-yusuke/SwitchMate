# Utilities Library

from .connect_wifi import connect_wifi
from .system import reboot, safe_reboot

__version__ = "1.0.0"
__all__ = [
    "connect_wifi",
    "reboot",
    "safe_reboot",
]
