# SwitchBot API Package
from .devices import DeviceAPI
from .scenes import SceneAPI
from .webhooks import WebhookAPI

__version__ = "1.0.0"
__all__ = ["DeviceAPI", "SceneAPI", "WebhookAPI"]
