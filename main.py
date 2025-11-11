from original_motion_sensor.factory import create_original_motion_sensor
from shared import get_logger

original_motion_sensor = create_original_motion_sensor()

app = create_original_motion_sensor()
logger = get_logger("main")


def setup():
    # Setup BLE connections to all bulbs
    if not app.setup_connections():
        logger.error("Failed to setup BLE connections to all bulbs")
        return
    logger.info("Application initialized successfully - all bulbs connected")


def loop():
    logger.info("Starting Original Motion Sensor")

    # Main loop
    try:
        while True:
            app.run()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        app.disconnect_ble()
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    setup()
    loop()
