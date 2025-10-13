"""
Infrastructure Layer - External system adapters and hardware abstractions
"""

# BLE
from .ble import BleClient, BleConnectionManager

# Hardware
from .hardware import Button, MotionSensor

# SwitchBot API
from .switchbot import ColorBulb, DeviceApi, SceneApi, WebhookApi

__version__ = "1.0.0"
__all__ = [
    # BLE
    "BleClient",
    "BleConnectionManager",
    # Hardware
    "Button",
    "MotionSensor",
    # SwitchBot API
    "ColorBulb",
    "DeviceApi",
    "SceneApi",
    "WebhookApi",
]
