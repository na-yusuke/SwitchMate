# SwitchMate Library Package

# SwitchBot API
from .switchbot import DeviceApi, SceneApi, WebhookApi

# Peripherals
from .peripherals import MotionSensor

__version__ = "1.0.0"
__all__ = [
    # SwitchBot API
    "DeviceApi", "SceneApi", "WebhookApi",
    # Peripherals
    "MotionSensor"
]