import machine
import network

from original_motion_sensor.factory import create_original_motion_sensor
from shared import LogLevel, configure, get_logger

original_motion_sensor = create_original_motion_sensor()

app = create_original_motion_sensor()
logger = get_logger("main")


def setup():
    # Downclock the CPU frequency to 80MHz for power saving
    machine.freq(80000000)

    # Disable Wi-Fi completely for power saving
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)

    # Clear RTC memory
    if machine.reset_cause() == machine.PWRON_RESET:
        rtc = machine.RTC()
        rtc.memory(b"")

    # Configure logging
    # LogLevel.DEBUG: Show all logs (development)
    # LogLevel.INFO: Show info and above (default)
    # LogLevel.WARNING: Show warnings and above (production)
    configure(level=LogLevel.DEBUG)

    # Setup BLE connections to all bulbs
    if not app.setup_connections():
        logger.error("Failed to setup BLE connections to all bulbs")
        return
    logger.info("Application initialized successfully - all bulbs connected")

    # After waking up from DeepSleep, turn on the color bulb
    if machine.reset_cause() == machine.DEEPSLEEP_RESET:
        logger.info("Woke up from deep sleep")
        app.power_on_bulbs_on_wakeup()


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
