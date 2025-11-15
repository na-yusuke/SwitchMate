import time

import bluetooth
from esp32 import WAKEUP_ANY_HIGH, wake_on_ext0
from machine import Pin, deepsleep, lightsleep

from infrastructure.hardware import Button, MotionSensor
from shared import get_logger, safe_reboot

from ..config.constants import (
    COLOR_BULB_CHECK_INTERVAL,
    DEEP_SLEEP_THRESHOLD,
    LIGHT_SLEEP_DURATION,
    LIGHT_SLEEP_THRESHOLD,
    POWER_ON_DURATION,
)
from ..domain import BulbAutomationService, ColorBulbManipulator, SleepActivityTracker

logger = get_logger("OriginalMotionSensor")


class OriginalMotionSensor:
    def __init__(
        self,
        motion_sensor: MotionSensor,
        button: Button,
        color_bulb_manipulator: ColorBulbManipulator,
        pir_pin: Pin,
    ) -> None:
        # Infrastructure
        self._motion_sensor: MotionSensor = motion_sensor
        self._button: Button = button
        self._color_bulb_manipulator: ColorBulbManipulator = color_bulb_manipulator
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

    def setup_connections(self) -> bool:
        """
        Setup BLE connections to all bulbs

        Returns:
            bool: True if all connections succeeded
        """
        logger.info("Setting up connections to all bulbs")
        return self._color_bulb_manipulator.connect_all()

    def disconnect_ble(self) -> None:
        """Disconnect from all bulbs to save power"""
        logger.info("Disconnecting from all bulbs")
        self._color_bulb_manipulator.disconnect_all()

    def power_on_bulbs_on_wakeup(self) -> None:
        """Power on bulbs after waking from deep sleep"""
        logger.info("Power on bulbs after deep sleep wakeup")
        self._color_bulb_manipulator.power_on_all()
        self._bulb_automation_service.record_last_motion_detected_time()

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
        Check if bulbs should auto power off
        """
        if not self._color_bulb_manipulator.is_any_powered_on():
            return

        if not self._bulb_automation_service.should_power_off_bulb():
            return

        logger.debug("Bulbs powered off due to elapsed time")
        self._color_bulb_manipulator.power_off_all()
        logger.debug("Bulbs powered off successfully")

        self._bulb_automation_service.reset_motion_detected_time()

    def __handle_motion_detected(self) -> None:
        # Always record motion detection time to reset the auto-off timer
        self._bulb_automation_service.record_last_motion_detected_time()

        if not self._color_bulb_manipulator.is_any_powered_on():
            logger.debug("Bulbs powered on by motion detection")
            self._color_bulb_manipulator.power_on_all()
            logger.debug("Bulbs powered on successfully")

    def __sync_bulb_status(self) -> None:
        if not self._bulb_automation_service.should_get_bulb_status():
            return

        logger.debug("Syncing bulbs status")
        self._bulb_automation_service.record_last_check_status_time()
        self._color_bulb_manipulator.sync_status_all()
        logger.debug("Bulbs status synced successfully")

    def __enter_light_sleep(self) -> None:
        """Enter light sleep mode (wake on GPIO interrupt)"""
        logger.info("No activity detected for a while, entering light sleep)")

        self._color_bulb_manipulator.prepare_for_sleep()

        # Waiting for motion sensor to go low
        while self._pir_pin.value() == 1:
            time.sleep_ms(100)

        wake_on_ext0(pin=self._pir_pin, level=WAKEUP_ANY_HIGH)

        lightsleep(LIGHT_SLEEP_DURATION)

    def __enter_deep_sleep(self) -> None:
        """Enter deep sleep mode"""
        logger.info("No activity detected for a while, entering deep sleep")

        self._color_bulb_manipulator.prepare_for_sleep()

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
