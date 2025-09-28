import time

import bluetooth

from config import SWITCHBOT_CHARACTERISTIC_UUID, SWITCHBOT_SERVICE_UUID
from device_config import DEVICE_CONFIG
from lib.ble import BleClient
from lib.peripherals import Button, MotionSensor
from lib.switchbot import ColorBulb


class OriginalMotionSensor:
    def __init__(self):
        self._client = BleClient(
            bluetooth.UUID(SWITCHBOT_SERVICE_UUID),
            bluetooth.UUID(SWITCHBOT_CHARACTERISTIC_UUID),
        )
        self._button = Button(25)
        # self._button.set_callback(self.setup_ble_connection())
        self._motion_sensor = MotionSensor(27)
        self._color_bulb = ColorBulb(self._client)

        self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1

    def setup_ble_connection(self):
        try:
            target_mac = DEVICE_CONFIG["color_bulb"]["corridor_light"]["ble_mac_address"]
            print(f"\n[1/4] Scanning for device: {target_mac}")
            if not self._client.scan_for_device(target_mac, 15000):
                print("Device not found")
                return

            print("\n[2/4] Connecting to device...")
            if not self._client.connect_to_target(10000):
                print("Connection failed")
                return
            print("Connected")

            print("\n[3/4] Discovering services...")
            self._client.discover_services()

            print("\n[4/4] Discovering characteristics...")
            self._client.discover_characteristics()
            print("Setup complete\n")
        except Exception as e:
            print(f"An error occurred: {e}")

        return self._client.is_connected()

    def disconnect_ble(self):
        print("Starting disconnect process")
        self._client.disconnect()
        print("Disconnect process completed")

    def run(self):
        """loop logic"""
        self._button.monitor()
        self.__power_off_bulb_based_elapsed_time()

        if self._motion_sensor.is_motion_detected():
            self._last_time_bulb_power_on = time.ticks_ms()
            self._color_bulb.power_on()

    def __power_off_bulb_based_elapsed_time(self):
        if time.ticks_diff(time.ticks_ms(), self._last_time_bulb_power_on) > 5000:
            self._color_bulb.power_off()
            self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1
