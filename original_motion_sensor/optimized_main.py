"""
最適化版モーションセンサー
- 高速再接続（1-3秒）
- 省電力（オンデマンドBLE接続）
"""

import time

import bluetooth

from config import SWITCHBOT_CHARACTERISTIC_UUID, SWITCHBOT_SERVICE_UUID
from device_config import DEVICE_CONFIG
from lib.ble import BleClient
from lib.ble.fast_reconnect_client import FastReconnectClient
from lib.peripherals import Button, MotionSensor
from lib.switchbot import ColorBulb
from utils import safe_reboot

from .constants import COLOR_BULB_CHECK_INTERVAL, POWER_ON_DURATION


class OptimizedMotionSensor:
    """最適化版モーションセンサークラス"""

    # 省電力設定
    IDLE_TIMEOUT = 30000  # 30秒間アイドルでBLE切断
    SCAN_TIMEOUT = 3000  # スキャンタイムアウト（3秒）
    CONNECT_TIMEOUT = 5000  # 接続タイムアウト（5秒）

    def __init__(self):
        self._target_mac = DEVICE_CONFIG["color_bulb"]["corridor_light"]["ble_mac_address"]

        # BleClientを作成
        self._client = BleClient(
            bluetooth.UUID(SWITCHBOT_SERVICE_UUID),
            bluetooth.UUID(SWITCHBOT_CHARACTERISTIC_UUID),
        )

        # 高速再接続クライアントでラップ
        self._fast_client = FastReconnectClient(self._client)

        self._button = Button(25)
        self._button.set_callback(self.__button_pressed_callback)
        self._motion_sensor = MotionSensor(27)
        self._color_bulb = ColorBulb(self._client)

        # 状態管理
        self._ble_connected = False
        self._last_time_checked_bulb_status = time.ticks_ms()
        self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1
        self._last_activity_time = 0

        # GATT handles のキャッシュ
        self._gatt_setup_done = False

    def setup_ble_connection(self):
        """BLE接続をセットアップ（高速再接続対応）"""
        if self._ble_connected and self._client.is_connected():
            print("[Optimized] Already connected")
            return True

        try:
            start_time = time.ticks_ms()

            # 高速再接続を試みる
            print(f"\n[Optimized] Connecting to {self._target_mac}...")
            if not self._fast_client.connect_with_cache(
                self._target_mac, scan_timeout_ms=self.SCAN_TIMEOUT, connect_timeout_ms=self.CONNECT_TIMEOUT
            ):
                print("[Optimized] Connection failed")
                return False

            connect_duration = time.ticks_diff(time.ticks_ms(), start_time)
            print(f"[Optimized] Connected in {connect_duration}ms")

            # GATT探索（初回のみ、または必要な場合のみ）
            if not self._gatt_setup_done:
                print("[Optimized] Discovering services and characteristics...")
                self._client.discover_services()
                self._client.discover_characteristics()
                self._gatt_setup_done = True
            else:
                print("[Optimized] Using cached GATT handles")

            total_duration = time.ticks_diff(time.ticks_ms(), start_time)
            print(f"[Optimized] Setup complete in {total_duration}ms\n")

            self._ble_connected = True
            return True

        except Exception as e:
            print(f"[Optimized] Error: {e}")
            return False

    def disconnect_ble(self):
        """BLE切断（省電力のため）"""
        if self._ble_connected:
            print("[Optimized] Disconnecting BLE to save power...")
            self._fast_client.disconnect()
            self._ble_connected = False
            print("[Optimized] BLE disconnected")

    def run(self):
        """メインループ（省電力 + 高速応答）"""
        self._button.monitor()

        # モーション検知時
        if self._motion_sensor.is_motion_detected():
            self.__handle_motion_detected()
            self._last_activity_time = time.ticks_ms()

        # LED自動消灯
        self.__power_off_bulb_based_elapsed_time()

        # アイドルタイムアウトでBLE切断（省電力）
        if self._ble_connected:
            idle_time = time.ticks_diff(time.ticks_ms(), self._last_activity_time)
            if idle_time > self.IDLE_TIMEOUT:
                self.disconnect_ble()

        # 定期的な状態同期（BLE接続中のみ）
        if self._ble_connected:
            self.__sync_bulb_status()

        # 軽いスリープ（CPUを休ませる）
        time.sleep_ms(100)

    def __button_pressed_callback(self):
        """ボタン押下時のコールバック"""
        safe_reboot()

    def __handle_motion_detected(self):
        """モーション検知時の処理"""
        print("[Optimized] Motion detected!")

        # BLE接続（必要な場合のみ）
        if not self._ble_connected:
            if not self.setup_ble_connection():
                print("[Optimized] Cannot control bulb - connection failed")
                return

        # LED点灯
        if not self._color_bulb.is_powered_on():
            self._last_time_bulb_power_on = time.ticks_ms()
            print("---- Bulb powered on by motion detection ----")
            self._color_bulb.power_on()
            print("---- Bulb powered on successfully ----\n")

    def __power_off_bulb_based_elapsed_time(self):
        """経過時間に基づいてLED消灯"""
        if (
            self._color_bulb.is_powered_on()
            and time.ticks_diff(time.ticks_ms(), self._last_time_bulb_power_on) > POWER_ON_DURATION
        ):
            # 消灯のためにBLE接続が必要
            if not self._ble_connected:
                if not self.setup_ble_connection():
                    return

            print("---- Bulb powered off due to elapsed time ----")
            self._color_bulb.power_off()
            print("---- Bulb powered off successfully ----\n")
            self._last_time_bulb_power_on = time.ticks_add(0, -1) / 2 - 1

    def __sync_bulb_status(self):
        """LED状態を定期的に同期"""
        if time.ticks_diff(time.ticks_ms(), self._last_time_checked_bulb_status) < COLOR_BULB_CHECK_INTERVAL:
            return
        self._last_time_checked_bulb_status = time.ticks_ms()

        if not self._ble_connected:
            return  # BLE切断中はスキップ

        print("---- Syncing bulb status... ----")
        if self._color_bulb.sync_status() is None:
            print("Failed to sync bulb status")
            # 接続が切れている可能性があるので再接続を試みる
            self._ble_connected = False
            self._gatt_setup_done = False  # 次回は再探索
            return
        print("---- Bulb status synced successfully ----\n")
        self._last_activity_time = time.ticks_ms()  # アクティビティタイムスタンプ更新


# 使用例
if __name__ == "__main__":
    sensor = OptimizedMotionSensor()

    # 初回接続
    if sensor.setup_ble_connection():
        print("Ready!")

        # メインループ
        try:
            while True:
                sensor.run()
        except KeyboardInterrupt:
            print("\nStopping...")
            sensor.disconnect_ble()
