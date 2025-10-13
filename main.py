from original_motion_sensor.factory import create_original_motion_sensor
from shared import get_logger

original_motion_sensor = create_original_motion_sensor()

logger = get_logger("main")


def setup():
    is_connected = False
    while not is_connected:
        is_connected = original_motion_sensor.setup_ble_connection()


def loop():
    logger.info("Starting Original Motion Sensor")

    # Create application instance
    app = create_original_motion_sensor()

    # Setup BLE connection
    if not app.setup_ble_connection():
        logger.error("Failed to setup BLE connection")
        return

    logger.info("Application initialized successfully")

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
