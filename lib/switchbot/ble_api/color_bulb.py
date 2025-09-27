"""Client class for Color Bulb BLE open API

https://github.com/OpenWonderLabs/SwitchBotAPI-BLE/blob/latest/devicetypes/colorbulb.md
"""

class ColorBulb:
    def __init__(self, ble_client):
        self.ble_client = ble_client
        pass

    def power_on(self):
        """Turn on the bulb"""
        command = bytes([0x57, 0x0f, 0x47, 0x01, 0x01])
        return self.ble_client.write_characteristic(command)
    
    def power_off(self):
        """Turn off the bulb"""
        command = bytes([0x57, 0x0f, 0x47, 0x01, 0x02])
        return self.ble_client.write_characteristic(command)
    
    def set_brightness(self, brightness):
        """Brightness (1-100)"""
        brightness = max(1, min(100, brightness))
        command = bytes([0x57, 0x0f, 0x47, 0x01, 0x14, brightness])
        return self.ble_client.write_characteristic(command)
