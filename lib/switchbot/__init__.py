# SwitchBot Library Package

# SwitchBot BLE API
from .ble_api import ColorBulb

# SwitchBot Web API
from .web_api import DeviceApi, SceneApi, WebhookApi

__version__ = "1.0.0"
__all__ = [
    # SwitchBot BLE API
    "ColorBulb",
    # SwitchBot Web API
    "DeviceApi",
    "SceneApi",
    "WebhookApi",
]
