import time

import bluetooth
from esp32 import WAKEUP_ANY_HIGH, wake_on_ext0
from machine import RTC, Pin, deepsleep, lightsleep

from config import SWITCHBOT_CHARACTERISTIC_UUID, SWITCHBOT_SERVICE_UUID
from device_config import DEVICE_CONFIG, MICROCONTROLLER_PIN_CONFIG
from lib.ble import BleClient, BleConnectionManager
from lib.logger import get_logger
from lib.peripherals import Button, MotionSensor
from lib.switchbot import ColorBulb
from utils import safe_reboot

from .constants import (
    COLOR_BULB_CHECK_INTERVAL,
    DEEP_SLEEP_THRESHOLD,
    LIGHT_SLEEP_DURATION,
    LIGHT_SLEEP_THRESHOLD,
    POWER_ON_DURATION,
)

logger = get_logger("OriginalMotionSensor")


class OriginalMotionSensor:
    def __init__(self):
        self._target_mac = DEVICE_CONFIG["color_bulb"]["corridor_light"]["ble_mac_address"]

        self._client = BleClient(
            bluetooth.UUID(SWITCHBOT_SERVICE_UUID),
            bluetooth.UUID(SWITCHBOT_CHARACTERISTIC_UUID),
        )
        self._ble_connection_manager = BleConnectionManager(self._client, self._target_mac)

        self._pir_pin = Pin(MICROCONTROLLER_PIN_CONFIG["motion_sensor"], Pin.IN)
        self._rtc = RTC()

        self._button = Button(MICROCONTROLLER_PIN_CONFIG["button"])
        self._button.set_callback(self.__button_pressed_callback)
        self._motion_sensor = MotionSensor(MICROCONTROLLER_PIN_CONFIG["motion_sensor"])
        self._color_bulb = ColorBulb(self._client)

        self._last_time_check_bulb_status = time.ticks_ms()
        self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1
        self._last_activity_time = time.ticks_add(0, -1) / 2 - 1

    def __button_pressed_callback(self):
        safe_reboot()

    def setup_ble_connection(self):
        if self._ble_connection_manager.ensure_connected():
            return True

        return False

    def disconnect_ble(self):
        if self._ble_connection_manager.is_connected():
            logger.info("Disconnecting BLE to save power")
            self._ble_connection_manager.disconnect()
            logger.info("BLE disconnected")

    def run(self):
        """loop logic"""

        # Monitor button
        self._button.monitor()

        # Auto power off bulb after duration
        self.__power_off_bulb_based_elapsed_time()

        # Monitor motion sensor
        if self._motion_sensor.is_motion_detected():
            self.__handle_motion_detected()
            self._last_activity_time = time.ticks_ms()
        else:
            if time.ticks_diff(time.ticks_ms(), self._last_activity_time) > DEEP_SLEEP_THRESHOLD:
                self.__enter_deep_sleep()
            if time.ticks_diff(time.ticks_ms(), self._last_activity_time) > LIGHT_SLEEP_THRESHOLD:
                self.__enter_light_sleep()

        # Sync bulb status periodically
        # self.__sync_bulb_status()

    def __handle_motion_detected(self):
        if not self._ble_connection_manager.ensure_connected():
            logger.error("Cannot control bulb - connection failed")
            return

        if not self._color_bulb.is_powered_on():
            self._last_time_bulb_power_on = time.ticks_ms()
            logger.debug("Bulb powered on by motion detection")
            self._color_bulb.power_on()
            logger.debug("Bulb powered on successfully")

    def __power_off_bulb_based_elapsed_time(self):
        if (
            self._color_bulb.is_powered_on()
            and time.ticks_diff(time.ticks_ms(), self._last_time_bulb_power_on) > POWER_ON_DURATION
        ):
            if not self._ble_connection_manager.ensure_connected():
                return
            logger.debug("Bulb powered off due to elapsed time")
            self._color_bulb.power_off()
            logger.debug("Bulb powered off successfully")
            self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1

    def __sync_bulb_status(self):
        if (
            time.ticks_diff(time.ticks_ms(), self._last_time_check_bulb_status) < COLOR_BULB_CHECK_INTERVAL
            or not self._ble_connection_manager.is_connected()
        ):
            return
        self._last_time_check_bulb_status = time.ticks_ms()

        logger.debug("Syncing bulb status")
        if self._color_bulb.sync_status() is None:
            logger.warning("Failed to sync bulb status")
            return
        logger.debug("Bulb status synced successfully")

    def __enter_light_sleep(self):
        """Enter light sleep mode (wake on GPIO interrupt)"""
        logger.info("No activity detected for a while, entering light sleep)")

        self._ble_connection_manager.prepare_for_sleep()

        # Waiting for motion sensor to go low
        while self._pir_pin.value() == 1:
            time.sleep_ms(100)

        wake_on_ext0(pin=self._pir_pin, level=WAKEUP_ANY_HIGH)

        lightsleep(LIGHT_SLEEP_DURATION)

    def __enter_deep_sleep(self):
        """Enter deep sleep mode"""
        logger.info("No activity detected for a while, entering deep sleep")

        self._ble_connection_manager.prepare_for_sleep()

        # Waiting for motion sensor to go low
        while self._pir_pin.value() == 1:
            time.sleep_ms(100)

        wake_on_ext0(pin=self._pir_pin, level=WAKEUP_ANY_HIGH)

        try:
            ble = bluetooth.BLE()
            ble.active(False)
        except Exception:
            pass

        deepsleep()
