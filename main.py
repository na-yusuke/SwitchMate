from original_motion_sensor.factory import create_original_motion_sensor

original_motion_sensor = create_original_motion_sensor()


def setup():
    is_connected = False
    while not is_connected:
        is_connected = original_motion_sensor.setup_ble_connection()


def loop():
    try:
        while True:
            original_motion_sensor.run()
    except KeyboardInterrupt:
        from lib.logger import get_logger

        logger = get_logger("Main")
        original_motion_sensor.disconnect_ble()
        logger.info("Process finished")


if __name__ == "__main__":
    setup()
    loop()
