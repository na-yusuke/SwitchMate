from .base import BaseAPI


class DeviceAPI(BaseAPI):
    """SwitchBot デバイス関連API"""

    def get_devices(self):
        """デバイス一覧を取得"""
        return self.__make_request('GET', '/devices')

    def get_device_status(self, device_id):
        """デバイスの状態を取得"""
        return self.__make_request('GET', f'/devices/{device_id}/status')

    def control_device(self, device_id, command, parameter=None):
        """デバイスを制御"""
        data = {
            'command': command,
            'parameter': parameter or 'default'
        }
        return self.__make_request('POST', f'/devices/{device_id}/commands', data)

    def print_devices(self):
        """デバイス一覧を見やすく表示"""
        devices_data = self.get_devices()

        if not devices_data:
            print("Failed to get devices")
            return

        if 'body' not in devices_data:
            print("No device data found")
            return

        body = devices_data['body']
        print("=== SwitchBot Devices ===")

        if 'deviceList' in body and body['deviceList']:
            print("\n[Physical Devices]")
            for device in body['deviceList']:
                print(f"- {device.get('deviceName', 'Unknown')} ({device.get('deviceType', 'Unknown')})")
                print(f"  ID: {device.get('deviceId', 'Unknown')}")
                if 'hubDeviceId' in device:
                    print(f"  Hub: {device['hubDeviceId']}")
                print()

        if 'infraredRemoteList' in body and body['infraredRemoteList']:
            print("[Virtual Infrared Devices]")
            for device in body['infraredRemoteList']:
                print(f"- {device.get('deviceName', 'Unknown')} ({device.get('remoteType', 'Unknown')})")
                print(f"  ID: {device.get('deviceId', 'Unknown')}")
                if 'hubDeviceId' in device:
                    print(f"  Hub: {device['hubDeviceId']}")
                print()

        print("========================")

    def turn_on_device(self, device_id):
        """SwitchBotをONにする"""
        return self.control_device(device_id, 'turnOn')

    def turn_off_device(self, device_id):
        """SwitchBotをOFFにする"""
        return self.control_device(device_id, 'turnOff')
