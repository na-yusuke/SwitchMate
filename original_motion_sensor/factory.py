import bluetooth
import machine
from machine import Pin

from config import SWITCHBOT_CHARACTERISTIC_UUID, SWITCHBOT_SERVICE_UUID
from device_config import DEVICE_CONFIG
from infrastructure.ble import BleConnectionPool
from infrastructure.hardware import Button, MotionSensor
from infrastructure.switchbot import ColorBulb
from original_motion_sensor.application import OriginalMotionSensor
from original_motion_sensor.domain import ColorBulbManipulator

from .config.constants import MICROCONTROLLER_PIN_CONFIG, TARGET_COLOR_BULBS


def create_original_motion_sensor():
    """
    Create and return an OriginalMotionSensor instance.
    """
    # Create BLE connection pool for managing multiple simultaneous connections
    connection_pool = BleConnectionPool(
        bluetooth.UUID(SWITCHBOT_SERVICE_UUID),
        bluetooth.UUID(SWITCHBOT_CHARACTERISTIC_UUID),
    )
    if machine.reset_cause() == machine.DEEPSLEEP_RESET:
        connection_pool.restore_addr_cache()

    # Create ColorBulb instances for each target device
    color_bulbs = []
    for bulb_name in TARGET_COLOR_BULBS:
        if bulb_name not in DEVICE_CONFIG.get("color_bulb", {}):
            raise ValueError(f"Device '{bulb_name}' not found in DEVICE_CONFIG")

        mac_address = DEVICE_CONFIG["color_bulb"][bulb_name]["ble_mac_address"]

        # Add device to connection pool
        connection_pool.add_device(mac_address)

        color_bulbs.append(ColorBulb(connection_pool.ble_client, mac_address))

    # Create ColorBulbManipulator with connection pool
    color_bulb_manipulator = ColorBulbManipulator(color_bulbs, connection_pool)

    # Create hardware components
    pir_pin = Pin(MICROCONTROLLER_PIN_CONFIG["motion_sensor"], Pin.IN)
    button = Button(MICROCONTROLLER_PIN_CONFIG["button"])
    motion_sensor = MotionSensor(MICROCONTROLLER_PIN_CONFIG["motion_sensor"])

    return OriginalMotionSensor(
        motion_sensor=motion_sensor,
        button=button,
        color_bulb_manipulator=color_bulb_manipulator,
        pir_pin=pir_pin,
    )
