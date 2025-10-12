# SwitchMate Library Package

# BLE
from .ble import BleClient, BleConnectionManager

# Peripherals
from .peripherals import Button, MotionSensor

# SwitchBot API
from .switchbot import ColorBulb, DeviceApi, SceneApi, WebhookApi

__version__ = "1.0.0"
__all__ = [
    # BLE
    "BleClient",
    "BleConnectionManager",
    # Peripherals
    "Button",
    "MotionSensor",
    # SwitchBot API
    "ColorBulb",
    "DeviceApi",
    "SceneApi",
    "WebhookApi",
]
