import time

import network

from config import DEBUG


def init_wifi():
    """Initialize Wi-Fi connection"""
    try:
        from config import WIFI_PASSWORD, WIFI_SSID

        if connect_wifi(WIFI_SSID, WIFI_PASSWORD):
            if DEBUG:
                print("Boot sequence completed successfully")
            return True
        else:
            print("Boot sequence failed - Wi-Fi connection error")
            return False

    except ImportError:
        print(
            "Error: config.py not found. Please create config.py with your Wi-Fi settings."
        )
        print("You can copy config_example.py and rename it to config.py")
        return False
    except Exception as e:
        print(f"Unexpected error during Wi-Fi initialization: {e}")
        return False


def connect_wifi(ssid, password, timeout=10):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("Already connected to Wi-Fi")
        print("Network config:", wlan.ifconfig())
        return True

    print("Connecting to Wi-Fi...")
    wlan.connect(ssid, password)

    start_time = time.time()
    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print("Wi-Fi connection timeout")
            return False
        time.sleep(0.5)
        print(".", end="")

    print("\nWi-Fi connected successfully!")
    print("Network config:", wlan.ifconfig())
    return True
