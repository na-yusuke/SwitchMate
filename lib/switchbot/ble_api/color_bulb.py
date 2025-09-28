"""Client class for Color Bulb BLE open API

https://github.com/OpenWonderLabs/SwitchBotAPI-BLE/blob/latest/devicetypes/colorbulb.md
"""


class ColorBulb:
    def __init__(self, ble_client):
        self.ble_client = ble_client
        self._last_status_response = None

    def power_on(self):
        """Turn on the bulb"""
        command = bytes([0x57, 0x0F, 0x47, 0x01, 0x01])
        return self.ble_client.write_characteristic(command)

    def power_off(self):
        """Turn off the bulb"""
        command = bytes([0x57, 0x0F, 0x47, 0x01, 0x02])
        return self.ble_client.write_characteristic(command)

    def set_brightness(self, brightness):
        """Brightness (1-100)"""
        brightness = max(1, min(100, brightness))
        command = bytes([0x57, 0x0F, 0x47, 0x01, 0x14, brightness])
        return self.ble_client.write_characteristic(command)

    def get_status(self, timeout_ms=5000):
        """Read bulb status and return parsed result"""
        # Correct command format: 0x570F4801 (4 bytes)
        command = bytes([0x57, 0x0F, 0x48, 0x01])
        print(f"Sending status request: {command.hex()}")

        # Send status request command
        if not self.ble_client.write_characteristic(command):
            print("Failed to send status request")
            return None

        # Wait for notification response
        response_data = self.ble_client.wait_for_notification(timeout_ms)
        if response_data is None:
            print("No response received within timeout")
            return None

        # Parse and return status
        return self.__parse_status_response(response_data)

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
            print(f"Invalid response length: {len(response_data) if response_data else 0}")
            return None

        if response_data[0] != 0x01:
            print(f"Invalid response header: 0x{response_data[0]:02X}")
            return None

        status = {
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

        return status

    def print_status(self, status):
        """Print formatted status information"""
        if not status:
            print("No status data available")
            return

        print("=== Color Bulb Status ===")
        print(f"Power: {'ON' if status['power_on'] else 'OFF'}")
        print(f"Brightness: {status['brightness']}%")
        print(f"RGB Color: R={status['rgb']['red']}, G={status['rgb']['green']}, B={status['rgb']['blue']}")
        print(f"Color Temperature: {status['color_temperature']}")
        print(f"Mode: 0x{status['mode']:06X}")
        print(f"Raw Data: {status['raw_data']}")
        print("========================")
