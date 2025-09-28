import hashlib
import time

import ntptime
import ubinascii
import ujson
import urequests

from config import DEBUG, SWITCHBOT_API_CLIENT_SECRET, SWITCHBOT_API_TOKEN, SWITCHBOT_BASE_URL
from lib.hmac import hmac


class BaseApi:
    """SwitchBot API base class"""

    def __init__(self):
        self.base_url = SWITCHBOT_BASE_URL
        self.token = SWITCHBOT_API_TOKEN
        self.secret = SWITCHBOT_API_CLIENT_SECRET
        self.timestamp = ""
        self._sync_time()

    def _sync_time(self):
        """Synchronize time via NTP"""
        try:
            ntptime.settime()
        except Exception:
            pass  # Continue even if NTP sync fails

        # Get current time in milliseconds
        # ESP32 timestamp needs to be milliseconds since Jan 1, 2000, but Unix time has been measured since Jan 1, 1970.
        # So add 946684800 seconds (30 years)
        self.timestamp = str(int((time.time() + 946684800) * 1000))

        if DEBUG:
            print(f"Timestamp: {self.timestamp}")

    def __generate_headers(self):
        """Generate headers for SwitchBot API"""
        nonce = ""

        # Generate signature
        string_to_sign = self.token + self.timestamp + nonce
        signature = (
            ubinascii.b2a_base64(
                hmac.new(
                    self.secret.encode("utf-8"),
                    string_to_sign.encode("utf-8"),
                    hashlib.sha256,
                ).digest()
            )
            .strip()
            .decode("utf-8")
        )

        return {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "charset": "utf8",
            "t": self.timestamp,
            "sign": signature,
            "nonce": nonce,
        }

    def __make_request(self, method, endpoint, data=None):
        """Common HTTP request processing"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self.__generate_headers()

            if DEBUG:
                print(f"Request: {method} {url}")
                print(f"Headers: {headers}")
                if data:
                    print(f"Data: {data}")

            if method.upper() == "GET":
                response = urequests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = urequests.post(url, headers=headers, data=ujson.dumps(data) if data else None)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if DEBUG:
                print(f"Response status: {response.status_code}")
                print(f"Response text: {response.text}")

            if response.status_code == 200:
                result = ujson.loads(response.text)
                response.close()
                return result
            else:
                if DEBUG:
                    print(f"API Error: {response.status_code}")
                response.close()
                return None

        except Exception as e:
            if DEBUG:
                print(f"Exception in __make_request: {e}")
            return None
