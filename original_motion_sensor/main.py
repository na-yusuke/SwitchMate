import time

import bluetooth

from config import SWITCHBOT_CHARACTERISTIC_UUID, SWITCHBOT_SERVICE_UUID
from device_config import DEVICE_CONFIG
from lib.ble import BleClient, FastReconnectClient
from lib.peripherals import Button, MotionSensor
from lib.switchbot import ColorBulb
from utils import safe_reboot

from .constants import BLE_IDLE_TIMEOUT, COLOR_BULB_CHECK_INTERVAL, POWER_ON_DURATION


class OriginalMotionSensor:
    def __init__(self):
        self._target_mac = DEVICE_CONFIG["color_bulb"]["corridor_light"]["ble_mac_address"]

        self._client = BleClient(
            bluetooth.UUID(SWITCHBOT_SERVICE_UUID),
            bluetooth.UUID(SWITCHBOT_CHARACTERISTIC_UUID),
        )
        self._fast_client = FastReconnectClient(self._client)

        self._button = Button(25)
        self._button.set_callback(self.__button_pressed_callback)
        self._motion_sensor = MotionSensor(27)
        self._color_bulb = ColorBulb(self._client)

        self._last_time_check_bulb_status = time.ticks_ms()
        self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1
        self._last_activity_time = time.ticks_add(0, -1) / 2 - 1

    def setup_ble_connection(self):
        if self._fast_client.is_connected():
            print("Already connected to BLE device")
            return True

        try:
            print(f"[OriginalMotionSensor] Scanning for device: {self._target_mac}\n")

            if not self._fast_client.connect_with_cache(
                self._target_mac,
            ):
                print("Connection failed")
                return False

            print("[OriginalMotionSensor] Setup complete\n")
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

        return True

    def disconnect_ble(self):
        if self._fast_client.is_connected():
            print("[Optimized] Disconnecting BLE to save power\n")
            self._fast_client.disconnect()
            print("[Optimized] BLE disconnected\n")

    def run(self):
        """loop logic"""
        # Monitor button
        self._button.monitor()

        # Monitor motion sensor
        if self._motion_sensor.is_motion_detected():
            self.__handle_motion_detected()
            self._last_activity_time = time.ticks_ms()

        # Auto power off bulb after duration
        self.__power_off_bulb_based_elapsed_time()

        # Auto disconnect BLE if idle
        if self._fast_client.is_connected():
            if time.ticks_diff(time.ticks_ms(), self._last_activity_time) > BLE_IDLE_TIMEOUT:
                print("[Optimized] BLE idle timeout reached, disconnecting")
                self.disconnect_ble()

        # Sync bulb status periodically
        self.__sync_bulb_status()

        time.sleep_ms(100)

    def __button_pressed_callback(self):
        safe_reboot()

    def __handle_motion_detected(self):
        if not self._fast_client.is_connected():
            if not self.setup_ble_connection():
                print("[Optimized] Cannot control bulb - connection failed")
                return

        if not self._color_bulb.is_powered_on():
            self._last_time_bulb_power_on = time.ticks_ms()
            print("---- Bulb powered on by the motion detection ----")
            self._color_bulb.power_on()
            print("---- Bulb powered on successfully ----\n")

    def __power_off_bulb_based_elapsed_time(self):
        if (
            self._color_bulb.is_powered_on()
            and time.ticks_diff(time.ticks_ms(), self._last_time_bulb_power_on) > POWER_ON_DURATION
        ):
            if not self._fast_client.is_connected() and not self.setup_ble_connection():
                return
            print("---- Bulb powered off due to elapsed time ----")
            self._color_bulb.power_off()
            print("---- Bulb powered off successfully ----\n")
            self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1

    def __sync_bulb_status(self):
        if (
            time.ticks_diff(time.ticks_ms(), self._last_time_check_bulb_status) < COLOR_BULB_CHECK_INTERVAL
            or not self._fast_client.is_connected()
        ):
            return
        self._last_time_check_bulb_status = time.ticks_ms()

        print("---- Syncing bulb status ----")
        if self._color_bulb.sync_status() is None:
            print("Failed to sync bulb status")
            return
        print("---- Bulb status synced successfully ----\n")
