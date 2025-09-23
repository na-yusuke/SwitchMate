from lib import MotionSensor


def run():
    motion_sensor = MotionSensor(27)
    while True:
        print(motion_sensor.is_motion_detected())
        