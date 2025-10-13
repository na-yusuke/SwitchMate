import bluetooth
from machine import Pin

from config import SWITCHBOT_CHARACTERISTIC_UUID, SWITCHBOT_SERVICE_UUID
from device_config import DEVICE_CONFIG, MICROCONTROLLER_PIN_CONFIG
from infrastructure.ble import BleClient, BleConnectionManager
from infrastructure.hardware import Button, MotionSensor
from infrastructure.switchbot import ColorBulb
from original_motion_sensor.application import OriginalMotionSensor


def create_original_motion_sensor():
    """
    Create and return an OriginalMotionSensor instance with real hardware dependencies.
    """
    target_mac = DEVICE_CONFIG["color_bulb"]["corridor_light"]["ble_mac_address"]

    client = BleClient(
        bluetooth.UUID(SWITCHBOT_SERVICE_UUID),
        bluetooth.UUID(SWITCHBOT_CHARACTERISTIC_UUID),
    )
    ble_connection_manager = BleConnectionManager(client, target_mac)
    color_bulb = ColorBulb(client)
    pir_pin = Pin(MICROCONTROLLER_PIN_CONFIG["motion_sensor"], Pin.IN)
    button = Button(MICROCONTROLLER_PIN_CONFIG["button"])
    motion_sensor = MotionSensor(MICROCONTROLLER_PIN_CONFIG["motion_sensor"])

    return OriginalMotionSensor(
        connection_manager=ble_connection_manager,
        motion_sensor=motion_sensor,
        button=button,
        color_bulb=color_bulb,
        pir_pin=pir_pin,
    )
