import time

import network

from lib.logger import get_logger

logger = get_logger("connect_wifi")


def init_wifi():
    """Initialize Wi-Fi connection"""
    try:
        from config import WIFI_PASSWORD, WIFI_SSID

        if connect_wifi(WIFI_SSID, WIFI_PASSWORD):
            logger.info("Boot sequence completed successfully")
            return True
        else:
            logger.error("Boot sequence failed - Wi-Fi connection error")
            return False

    except ImportError:
        logger.error("Error: config.py not found. Please create config.py with your Wi-Fi settings.")
        logger.error("You can copy config_example.py and rename it to config.py")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Wi-Fi initialization: {e}")
        return False


def connect_wifi(ssid, password, timeout_ms=10000):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        logger.info("Already connected to Wi-Fi")
        logger.info("Network config:", wlan.ifconfig())
        return True

    logger.info("Connecting to Wi-Fi...")
    wlan.connect(ssid, password)

    start = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
            logger.error("Wi-Fi connection timeout")
            return False
        time.sleep(0.5)
        logger.info(".", end="")

    logger.info("\nWi-Fi connected successfully!")
    logger.info("Network config:", wlan.ifconfig())
    return True
