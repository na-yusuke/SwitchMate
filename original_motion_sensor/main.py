import bluetooth
import time

from config import SWITCHBOT_SERVICE_UUID, SWITCHBOT_CHARACTERISTIC_UUID
from device_config import DEVICE_CONFIG
from lib.ble import BleClient
from lib.switchbot import ColorBulb


def run():
    client = BleClient(
        bluetooth.UUID(SWITCHBOT_SERVICE_UUID),
        bluetooth.UUID(SWITCHBOT_CHARACTERISTIC_UUID),
    )
    color_bulb = ColorBulb(client)

    try:
        # Set a taget device's BLE MacAddress from DEVICE_CONFIG
        target_mac = DEVICE_CONFIG["color_bulb"]["desk_light"]["ble_mac_address"]

        # Step 1: Device scan
        if not client.scan_for_device(target_mac, 15000):
            print("Target device not found")
            return

        # Step 2: Connect
        if not client.connect_to_target(10000):
            print("Connection failed")
            return
        print("Connection successful")

        # Step 3: Discover service
        client.discover_services()
        time.sleep(2)

        # Step 4: Discover characteristic
        client.discover_characteristics()
        time.sleep(2)

        # Step 5: Run command
        if client._char_handle:
            print("SwitchBot Characteristic already discovered")

            color_bulb.power_off()
            time.sleep(2)

            color_bulb.power_on()
            time.sleep(2)
        else:
            print("SwitchBot Characteristic not found")

        # Step 6: After command
        print("Maintaining connection for 5 seconds...")
        time.sleep(5)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Step 7: Disconnect
        print("Starting disconnect process")
        client.disconnect()
        print("Process completed")
