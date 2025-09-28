from original_motion_sensor.main import OriginalMotionSensor

original_motion_sensor = OriginalMotionSensor()


def setup():
    if original_motion_sensor.setup_ble_connection():
        pass
    else:
        return


def loop():
    try:
        while True:
            original_motion_sensor.run()
    except KeyboardInterrupt:
        original_motion_sensor.disconnect_ble()
        print("\nFinish process")


if __name__ == "__main__":
    setup()
    loop()
