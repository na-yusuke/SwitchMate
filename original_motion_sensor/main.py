import json
import time

import bluetooth
from esp32 import WAKEUP_ANY_HIGH, wake_on_ext0
from machine import RTC, Pin, deepsleep, lightsleep

from config import SWITCHBOT_CHARACTERISTIC_UUID, SWITCHBOT_SERVICE_UUID
from device_config import DEVICE_CONFIG, MICROCONTROLLER_PIN_CONFIG
from lib.ble import BleClient, FastReconnectClient
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
        self._fast_client = FastReconnectClient(self._client)

        self._pir_pin = Pin(MICROCONTROLLER_PIN_CONFIG["motion_sensor"], Pin.IN)
        self._button_pin = Pin(MICROCONTROLLER_PIN_CONFIG["button"], Pin.IN, Pin.PULL_UP)
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
        if self._fast_client.is_connected():
            logger.info("Already connected to BLE device")
            return True

        self.__restore_ble_addr_info()

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

        # Auto power off bulb after duration
        self.__power_off_bulb_based_elapsed_time()

        # Monitor motion sensor
        if self._motion_sensor.is_motion_detected():
            self.__handle_motion_detected()
            self._last_activity_time = time.ticks_ms()
        else:
            if time.ticks_diff(time.ticks_ms(), self._last_activity_time) > LIGHT_SLEEP_THRESHOLD:
                self.__enter_light_sleep()
            if time.ticks_diff(time.ticks_ms(), self._last_activity_time) > DEEP_SLEEP_THRESHOLD:
                self.__enter_deep_sleep()

        # Sync bulb status periodically
        # self.__sync_bulb_status()

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

    def __enter_light_sleep(self):
        """Enter light sleep mode (wake on GPIO interrupt)"""
        logger.info("No activity detected for a while, entering light sleep)")

        # Waiting for motion sensor to go low
        while self._pir_pin.value() == 1:
            time.sleep_ms(100)

        wake_on_ext0(pin=self._pir_pin, level=WAKEUP_ANY_HIGH)

        lightsleep(LIGHT_SLEEP_DURATION)

    def __enter_deep_sleep(self):
        """Enter deep sleep mode"""
        logger.info("No activity detected for a while, entering deep sleep")

        # Waiting for motion sensor to go low
        while self._pir_pin.value() == 1:
            time.sleep_ms(100)

        # Cache address info for fast reconnection after waking up
        (
            addr_type,
            addr_bytes,
        ) = self._fast_client.client.get_addr_info()
        if addr_type is not None or addr_bytes is not None:
            self._rtc.memory(json.dumps({"addr_type": addr_type, "addr_bytes": addr_bytes}).encode())

        wake_on_ext0(pin=self._pir_pin, level=WAKEUP_ANY_HIGH)

        try:
            ble = bluetooth.BLE()
            ble.active(False)
        except Exception:
            pass

        deepsleep()

    def __restore_ble_addr_info(self):
        """Restore BLE address info from RTC memory for fast reconnection"""
        try:
            mem = self._rtc.memory()
            if not mem:
                return
            data = json.loads(mem.decode())
            addr_type = data.get("addr_type")
            addr_bytes = data.get("addr_bytes")
            if addr_type is not None and addr_bytes is not None:
                self._fast_client.client.restore_addr_info(addr_type, addr_bytes)
                logger.info("Restored BLE address info from RTC memory")
        except Exception as e:
            logger.error(f"Failed to restore BLE address info: {e}")
