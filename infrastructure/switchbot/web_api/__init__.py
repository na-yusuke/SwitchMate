# SwitchBot Web API Package
from .devices import DeviceApi
from .scenes import SceneApi
from .webhooks import WebhookApi

__version__ = "1.0.0"
__all__ = ["DeviceApi", "SceneApi", "WebhookApi"]
