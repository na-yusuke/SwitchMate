import time

import machine

from .logger import get_logger

logger = get_logger("System")


def reboot(delay_sec: int = 0) -> None:
    """
    Reboot ESP32 after an optional delay.

    Args:
        delay_sec: Delay in seconds before rebooting. Default is 0 (immediate reboot).
    """
    if delay_sec > 0:
        logger.warning(f"Rebooting in {delay_sec} seconds...")
        time.sleep(delay_sec)

    logger.warning("Rebooting now...")
    machine.reset()


def safe_reboot() -> None:
    """Safely reboot the ESP32 by deactivating BLE if active."""
    try:
        import bluetooth

        ble = bluetooth.BLE()
        ble.active(False)
        logger.info("BLE deactivated")
    except Exception as e:
        logger.error(f"Error deactivating BLE: {e}")

    reboot(delay_sec=1)
