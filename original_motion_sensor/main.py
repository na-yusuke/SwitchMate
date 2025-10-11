import time

import bluetooth

from config import SWITCHBOT_CHARACTERISTIC_UUID, SWITCHBOT_SERVICE_UUID
from device_config import DEVICE_CONFIG
from lib.ble import BleClient
from lib.peripherals import Button, MotionSensor
from lib.switchbot import ColorBulb
from utils import safe_reboot

from .constants import COLOR_BULB_CHECK_INTERVAL, POWER_ON_DURATION


class OriginalMotionSensor:
    def __init__(self):
        self._target_mac = DEVICE_CONFIG["color_bulb"]["corridor_light"]["ble_mac_address"]
        self._client = BleClient(
            bluetooth.UUID(SWITCHBOT_SERVICE_UUID),
            bluetooth.UUID(SWITCHBOT_CHARACTERISTIC_UUID),
        )
        self._button = Button(25)
        self._button.set_callback(self.__button_pressed_callback)
        self._motion_sensor = MotionSensor(27)
        self._color_bulb = ColorBulb(self._client)

        self._last_time_checke_bulb_status = time.ticks_ms()
        self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1

    def setup_ble_connection(self):
        if self._client.is_connected():
            print("Already connected to BLE device")
            return True

        try:
            print(f"\n[1/4] Scanning for device: {self._target_mac}")
            if not self._client.scan_for_device(self._target_mac, 15000):
                print("Device not found")
                return False

            print("\n[2/4] Connecting to device...")
            if not self._client.connect_to_target(5000):
                print("Connection failed")
                return False
            print("Connected")

            print("\n[3/4] Discovering services...")
            self._client.discover_services()

            print("\n[4/4] Discovering characteristics...")
            self._client.discover_characteristics()
            print("Setup complete\n")
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

        return True

    def disconnect_ble(self):
        print("Starting disconnect process")
        self._client.disconnect()
        print("Disconnect process completed")

    def run(self):
        """loop logic"""
        self._button.monitor()
        self.__power_off_bulb_based_elapsed_time()
        self.__power_on_bulb()
        self.__sync_bulb_status()

    def __button_pressed_callback(self):
        safe_reboot()

    def __power_on_bulb(self):
        if self._motion_sensor.is_motion_detected() and not self._color_bulb.is_powered_on():
            self._last_time_bulb_power_on = time.ticks_ms()
            print("---- Bulb powerd on by the motion detection ----")
            self._color_bulb.power_on()
            print("---- Bulb powered on successfully ----\n")

    def __power_off_bulb_based_elapsed_time(self):
        if (
            self._color_bulb.is_powered_on()
            and time.ticks_diff(time.ticks_ms(), self._last_time_bulb_power_on) > POWER_ON_DURATION
        ):
            print("---- Bulb powered off due to elapsed time ----")
            self._color_bulb.power_off()
            print("---- Bulb powered off successfully ----\n")
            self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1

    def __sync_bulb_status(self):
        if time.ticks_diff(time.ticks_ms(), self._last_time_checke_bulb_status) < COLOR_BULB_CHECK_INTERVAL:
            return
        self._last_time_checke_bulb_status = time.ticks_ms()

        if not self._client.is_connected():
            print("BLE not connected, attempting to connect...\n")
            if not self.setup_ble_connection():
                print("Failed to connect to BLE device")
                return

        print("---- Syncing bulb status... ----")
        if self._color_bulb.sync_status() is None:
            print("Failed to sync bulb status")
            return
        print("---- Bulb status synced successfully ----\n")
