"""Client class for Color Bulb BLE open API

https://github.com/OpenWonderLabs/SwitchBotAPI-BLE/blob/latest/devicetypes/colorbulb.md
"""

from lib.ble import BleClient
from lib.logger import get_logger

logger = get_logger("ColorBulb")


class ColorBulb:
    def __init__(self, ble_client: BleClient):
        self._ble_client = ble_client
        self._status = {
            "power_on": False,
            "brightness": 0,
            "rgb": {"red": 0, "green": 0, "blue": 0},
            "color_temperature": 0,
            "mode": 0,
            "raw_data": "",
        }

    def power_on(self):
        """Turn on the bulb"""
        command = bytes([0x57, 0x0F, 0x47, 0x01, 0x01])
        self._status.update(power_on=True)
        return self._ble_client.write_characteristic(command)

    def power_off(self):
        """Turn off the bulb"""
        command = bytes([0x57, 0x0F, 0x47, 0x01, 0x02])
        self._status.update(power_on=False)
        return self._ble_client.write_characteristic(command)

    def is_powered_on(self):
        """Return current power state"""
        return self._status.get("power_on", False)

    def set_brightness(self, brightness):
        """Brightness (1-100)"""
        brightness = max(1, min(100, brightness))
        command = bytes([0x57, 0x0F, 0x47, 0x01, 0x14, brightness])
        return self._ble_client.write_characteristic(command)

    def sync_status(self, timeout_ms=5000):
        """Read bulb status and return parsed result"""
        # Correct command format: 0x570F4801 (4 bytes)
        command = bytes([0x57, 0x0F, 0x48, 0x01])
        logger.debug(f"Requesting status: {command.hex()}")

        # Send status request command
        if not self._ble_client.write_characteristic(command):
            logger.error("Failed to send status request")
            return None

        # Wait for notification response
        response_data = self._ble_client.wait_for_notification(timeout_ms)
        if response_data is None:
            logger.warning("Status sync timeout")
            return None

        self._status = self.__parse_status_response(response_data)
        logger.info("Status synced successfully")
        return self._status

    def __parse_status_response(self, response_data):
        """Parse bulb status response

        Response format (11 bytes):
        - Byte 0: 0x01 (fixed)
        - Byte 1: Power and light status
        - Byte 2: Brightness (0-100%)
        - Bytes 3-5: RGB color values (0-255 each)
        - Bytes 6-7: Color temperature
        - Bytes 8-10: Bulb mode
        https://github.com/OpenWonderLabs/SwitchBotAPI-BLE/blob/latest/devicetypes/colorbulb.md#0x570f4801-read-the-status-of-bulb

        Returns dict with parsed status or None if invalid
        """
        if not response_data or len(response_data) < 11:
            logger.error(f"Invalid response length: {len(response_data) if response_data else 0}")
            return None

        if response_data[0] != 0x01:
            logger.error(f"Invalid response header: 0x{response_data[0]:02X}")
            return None

        return {
            "power_on": bool(response_data[1] & 0x80),  # Bit 7
            "brightness": response_data[2],
            "rgb": {
                "red": response_data[3],
                "green": response_data[4],
                "blue": response_data[5],
            },
            "color_temperature": (response_data[6] << 8) | response_data[7],
            "mode": (response_data[8] << 16) | (response_data[9] << 8) | response_data[10],
            "raw_data": response_data.hex(),
        }

    def print_status(self):
        """Print formatted status information"""
        if not self._status:
            logger.warning("No status data available")
            return

        logger.info("=== Color Bulb Status ===")
        power_state = "ON" if self._status.get("power_on") else "OFF"
        logger.info(f"Power: {power_state}")
        logger.info(f"Brightness: {self._status.get('brightness')}%")
        rgb = self._status.get("rgb", {})
        logger.info(f"RGB Color: R={rgb.get('red')}, G={rgb.get('green')}, B={rgb.get('blue')}")
        logger.info(f"Color Temperature: {self._status.get('color_temperature')}K")
        logger.info(f"Mode: 0x{self._status.get('mode'):06X}")
        logger.info(f"Raw Data: {self._status.get('raw_data')}")
        logger.info("========================")
