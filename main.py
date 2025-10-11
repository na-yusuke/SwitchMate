from lib.logger import LogLevel, configure
from original_motion_sensor.main import OriginalMotionSensor

# Configure logging - adjust level as needed
# LogLevel.DEBUG: Show all logs (development)
# LogLevel.INFO: Show info and above (default)
# LogLevel.WARNING: Show warnings and above (production)
configure(level=LogLevel.INFO)

original_motion_sensor = OriginalMotionSensor()


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
