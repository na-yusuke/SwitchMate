import time

import bluetooth

from config import SWITCHBOT_CHARACTERISTIC_UUID, SWITCHBOT_SERVICE_UUID
from device_config import DEVICE_CONFIG
from lib.ble import BleClient, FastReconnectClient
from lib.logger import get_logger
from lib.peripherals import Button, MotionSensor
from lib.switchbot import ColorBulb
from utils import safe_reboot

from .constants import BLE_IDLE_TIMEOUT, COLOR_BULB_CHECK_INTERVAL, POWER_ON_DURATION

logger = get_logger("OriginalMotionSensor")


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
            logger.info("Already connected to BLE device")
            return True

        try:
            logger.info(f"Scanning for device: {self._target_mac}")

            if not self._fast_client.connect_with_cache(
                self._target_mac,
            ):
                logger.error("Connection failed")
                return False

            logger.info("Setup complete")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return False

        return True

    def disconnect_ble(self):
        if self._fast_client.is_connected():
            logger.info("Disconnecting BLE to save power")
            self._fast_client.disconnect()
            logger.info("BLE disconnected")

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
                logger.info("BLE idle timeout reached, disconnecting")
                self.disconnect_ble()

        # Sync bulb status periodically
        self.__sync_bulb_status()

        time.sleep_ms(100)

    def __button_pressed_callback(self):
        safe_reboot()

    def __handle_motion_detected(self):
        if not self._fast_client.is_connected():
            if not self.setup_ble_connection():
                logger.error("Cannot control bulb - connection failed")
                return

        if not self._color_bulb.is_powered_on():
            self._last_time_bulb_power_on = time.ticks_ms()
            logger.info("Bulb powered on by motion detection")
            self._color_bulb.power_on()
            logger.info("Bulb powered on successfully")

    def __power_off_bulb_based_elapsed_time(self):
        if (
            self._color_bulb.is_powered_on()
            and time.ticks_diff(time.ticks_ms(), self._last_time_bulb_power_on) > POWER_ON_DURATION
        ):
            if not self._fast_client.is_connected() and not self.setup_ble_connection():
                return
            logger.info("Bulb powered off due to elapsed time")
            self._color_bulb.power_off()
            logger.info("Bulb powered off successfully")
            self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1

    def __sync_bulb_status(self):
        if (
            time.ticks_diff(time.ticks_ms(), self._last_time_check_bulb_status) < COLOR_BULB_CHECK_INTERVAL
            or not self._fast_client.is_connected()
        ):
            return
        self._last_time_check_bulb_status = time.ticks_ms()

        logger.debug("Syncing bulb status")
        if self._color_bulb.sync_status() is None:
            logger.warning("Failed to sync bulb status")
            return
        logger.debug("Bulb status synced successfully")
