import time

import machine


def reboot(delay_sec=0):
    """
    Reboot ESP32 after an optional delay.

    Args:
        delay_sec: Delay in seconds before rebooting. Default is 0 (immediate reboot).
    """
    if delay_sec > 0:
        print(f"Rebooting in {delay_sec} seconds...")
        time.sleep(delay_sec)

    print("Rebooting now...")
    machine.reset()


def safe_reboot():
    """Safely reboot the ESP32 by deactivating BLE if active."""
    try:
        import bluetooth

        ble = bluetooth.BLE()
        ble.active(False)
        print("BLE deactivated")
    except Exception as e:
        print(f"Error deactivating BLE: {e}")

    reboot(delay_sec=1)
