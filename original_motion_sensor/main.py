import time

from lib import DeviceApi, MotionSensor


def run():
    motion_sensor = MotionSensor(27)
    while True:
        print(motion_sensor.is_motion_detected())
        time.sleep(1)
        

def temp():
    device_api = DeviceApi()
    print("=== Retrieving Device List ===")
    device_api.print_devices()
