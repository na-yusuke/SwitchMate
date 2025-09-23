import hashlib
import ntptime
import ubinascii
import urequests
import ujson
import time

from lib.hmac import hmac

from config import SWITCHBOT_BASE_URL, SWITCHBOT_API_TOKEN, SWITCHBOT_API_CLIENT_SECRET, DEBUG


class SwitchBotAPI:
    def __init__(self):
        self.base_url = SWITCHBOT_BASE_URL
        self.token = SWITCHBOT_API_TOKEN
        self.secret = SWITCHBOT_API_CLIENT_SECRET
        self.timestamp = ""
        self.__sync_time()
    
    def __sync_time(self):
        try:
            ntptime.settime()
        except:
            pass  # NTP同期に失敗しても続行

        # 現在時刻をミリ秒で取得
        # ESP32のtimestampは2000年1月1日からのミリ秒である必要があるため、946684800秒（30年）を加算
        self.timestamp = str(int((time.time() + 946684800) * 1000))

        if DEBUG:
            print(f"Timestamp: {self.timestamp}")

    def __generate_headers(self):
        """SwitchBot API用のヘッダーを生成"""
        nonce = ""

        if DEBUG:
            print(f"Timestamp: {self.timestamp}")

        # 署名を生成
        string_to_sign = self.token + self.timestamp + nonce
        signature = ubinascii.b2a_base64(
            hmac.new(
                self.secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).strip().decode('utf-8')

        return {
            'Authorization': self.token,
            'Content-Type': 'application/json',
            'charset': 'utf8',
            't': self.timestamp,
            'sign': signature,
            'nonce': nonce
        }

    def get_devices(self):
        """デバイス一覧を取得"""
        try:
            url = f"{self.base_url}/devices"
            headers = self.__generate_headers()

            if DEBUG:
                print(f"Requesting: {url}")
                print(f"Headers: {headers}")

            response = urequests.get(url, headers=headers)

            if DEBUG:
                print(f"Response status: {response.status_code}")
                print(f"Response text: {response.text}")

            if response.status_code == 200:
                data = ujson.loads(response.text)
                response.close()
                return data
            else:
                if DEBUG:
                    print(f"API Error: {response.status_code}")
                response.close()
                return None

        except Exception as e:
            if DEBUG:
                print(f"Exception in get_devices: {e}")
            return None

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

        # 物理デバイス
        if 'deviceList' in body and body['deviceList']:
            print("\n[Physical Devices]")
            for device in body['deviceList']:
                print(f"- {device.get('deviceName', 'Unknown')} ({device.get('deviceType', 'Unknown')})")
                print(f"  ID: {device.get('deviceId', 'Unknown')}")
                if 'hubDeviceId' in device:
                    print(f"  Hub: {device['hubDeviceId']}")
                print()

        # 仮想デバイス
        if 'infraredRemoteList' in body and body['infraredRemoteList']:
            print("[Virtual Infrared Devices]")
            for device in body['infraredRemoteList']:
                print(f"- {device.get('deviceName', 'Unknown')} ({device.get('remoteType', 'Unknown')})")
                print(f"  ID: {device.get('deviceId', 'Unknown')}")
                if 'hubDeviceId' in device:
                    print(f"  Hub: {device['hubDeviceId']}")
                print()

        print("========================")
