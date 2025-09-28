# SwitchMate Library Package

# BLE
from .ble import BleClient

# Peripherals
from .peripherals import MotionSensor

# SwitchBot API
from .switchbot import ColorBulb, DeviceApi, SceneApi, WebhookApi

__version__ = "1.0.0"
__all__ = [
    # BLE
    "BleClient",
    # Peripherals
    "MotionSensor",
    # SwitchBot API
    "ColorBulb",
    "DeviceApi",
    "SceneApi",
    "WebhookApi",
]
