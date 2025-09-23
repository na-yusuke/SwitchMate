# SwitchMate Library Package

# SwitchBot API
from .switchbot import DeviceAPI, SceneAPI, WebhookAPI

# Peripherals
from .peripherals import MotionSensor

__version__ = "1.0.0"
__all__ = [
    # SwitchBot API
    "DeviceAPI", "SceneAPI", "WebhookAPI",
    # Peripherals
    "MotionSensor"
]