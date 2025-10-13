import time

import bluetooth
from esp32 import WAKEUP_ANY_HIGH, wake_on_ext0
from machine import Pin, deepsleep, lightsleep

from device_config import DEVICE_CONFIG
from lib.ble import BleConnectionManager
from lib.peripherals import Button, MotionSensor
from lib.switchbot import ColorBulb
from utils import get_logger, safe_reboot

from ..config.constants import (
    COLOR_BULB_CHECK_INTERVAL,
    DEEP_SLEEP_THRESHOLD,
    LIGHT_SLEEP_DURATION,
    LIGHT_SLEEP_THRESHOLD,
    POWER_ON_DURATION,
)
from ..domain import BulbAutomationService, SleepActivityTracker

logger = get_logger("OriginalMotionSensor")


class OriginalMotionSensor:
    def __init__(
        self,
        connection_manager: BleConnectionManager,
        motion_sensor: MotionSensor,
        button: Button,
        color_bulb: ColorBulb,
        pir_pin: Pin,
    ) -> None:
        self._target_mac: str = DEVICE_CONFIG["color_bulb"]["corridor_light"]["ble_mac_address"]

        # Infrastructure
        self._ble_connection_manager: BleConnectionManager = connection_manager
        self._motion_sensor: MotionSensor = motion_sensor
        self._button: Button = button
        self._color_bulb: ColorBulb = color_bulb
        self._pir_pin: Pin = pir_pin

        # Business logic
        self._bulb_automation_service: BulbAutomationService = BulbAutomationService(
            POWER_ON_DURATION, COLOR_BULB_CHECK_INTERVAL
        )
        self._sleep_activity_tracker: SleepActivityTracker = SleepActivityTracker(
            LIGHT_SLEEP_THRESHOLD, DEEP_SLEEP_THRESHOLD
        )

        self._button.set_callback(self.__button_pressed_callback)

    def __button_pressed_callback(self) -> None:
        safe_reboot()

    def setup_ble_connection(self) -> bool:
        if self._ble_connection_manager.ensure_connected():
            return True

        return False

    def disconnect_ble(self) -> None:
        if self._ble_connection_manager.is_connected():
            logger.info("Disconnecting BLE to save power")
            self._ble_connection_manager.disconnect()
            logger.info("BLE disconnected")

    def run(self) -> None:
        """loop logic"""

        # Monitor button
        self._button.monitor()

        # Auto power off bulb after duration
        self.__check_auto_power_off()

        # Monitor motion sensor
        if self._motion_sensor.is_motion_detected():
            self.__handle_motion_detected()
            self._sleep_activity_tracker.record_activity()
        else:
            if self._sleep_activity_tracker.should_enter_deep_sleep():
                self.__enter_deep_sleep()
            elif self._sleep_activity_tracker.should_enter_light_sleep():
                self.__enter_light_sleep()

    def __check_auto_power_off(self) -> None:
        """
        Check if bulb should auto power off
        """
        if not self._color_bulb.is_powered_on():
            return

        if not self._bulb_automation_service.should_power_off_bulb():
            return

        if not self._ble_connection_manager.ensure_connected():
            return

        logger.debug("Bulb powered off due to elapsed time")
        self._color_bulb.power_off()
        logger.debug("Bulb powered off successfully")

        self._bulb_automation_service.reset_power_on_time()

    def __handle_motion_detected(self) -> None:
        if not self._ble_connection_manager.ensure_connected():
            logger.error("Cannot control bulb - connection failed")
            return

        if not self._color_bulb.is_powered_on():
            logger.debug("Bulb powered on by motion detection")
            self._bulb_automation_service.record_last_power_on_time()
            self._color_bulb.power_on()
            logger.debug("Bulb powered on successfully")

    def __sync_bulb_status(self) -> None:
        if not self._bulb_automation_service.should_get_bulb_status():
            return

        logger.debug("Syncing bulb status")
        self._bulb_automation_service.record_last_check_status_time()
        if self._color_bulb.sync_status() is None:
            logger.warning("Failed to sync bulb status")
            return
        logger.debug("Bulb status synced successfully")

    def __enter_light_sleep(self) -> None:
        """Enter light sleep mode (wake on GPIO interrupt)"""
        logger.info("No activity detected for a while, entering light sleep)")

        self._ble_connection_manager.prepare_for_sleep()

        # Waiting for motion sensor to go low
        while self._pir_pin.value() == 1:
            time.sleep_ms(100)

        wake_on_ext0(pin=self._pir_pin, level=WAKEUP_ANY_HIGH)

        lightsleep(LIGHT_SLEEP_DURATION)

    def __enter_deep_sleep(self) -> None:
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
