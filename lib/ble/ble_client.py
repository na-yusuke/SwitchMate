import bluetooth
from micropython import const
import time

# BLE定数
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)


class BleClient:
    def __init__(self, service_uuid, caracteristic_uuid):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self.__irq)
        self.__reset()

        self._service_uuid = service_uuid
        self._caracteristic_uuid = caracteristic_uuid

    def __reset(self):
        self._conn_handle = None
        self._start_handle = None
        self._end_handle = None
        self._char_handle = None
        self._notify_handle = None
        self._is_connected = False
        self._scan_callback = None
        self._is_target_found = False
        self._target_addr_bytes = None
        self._target_addr_type = None

    def __irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            addr_str = self.__addr_to_str(addr)
            print(f"デバイス発見: {addr_str}, RSSI: {rssi}")
            
            if self._scan_callback:
                self._scan_callback(addr_type, addr, adv_type, rssi, adv_data)

        elif event == _IRQ_SCAN_DONE:
            print("スキャン完了")

        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            print(f"接続成功: {self.__addr_to_str(addr)}")
            self._conn_handle = conn_handle
            self._is_connected = True

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            print(f"切断: {self.__addr_to_str(addr)}")
            self.__reset()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            print(f"サービス発見: {uuid}")
            if uuid == self._service_uuid:
                self._start_handle = start_handle
                self._end_handle = end_handle
                print(f"SwitchBotサービス発見: {start_handle}-{end_handle}")

        elif event == _IRQ_GATTC_SERVICE_DONE:
            conn_handle, status = data
            print(f"サービス発見完了: status={status}")

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            print(f"Characteristic発見: {uuid}, handle={value_handle}")
            if uuid == self._caracteristic_uuid:
                self._char_handle = value_handle
                print(f"SwitchBot Characteristic発見: handle={value_handle}")

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            conn_handle, status = data
            print(f"Characteristic発見完了: status={status}")

        elif event == _IRQ_GATTC_READ_RESULT:
            conn_handle, value_handle, char_data = data
            print(f"読み取り結果: {char_data}")

        elif event == _IRQ_GATTC_READ_DONE:
            conn_handle, value_handle, status = data
            print(f"読み取り完了: status={status}")

        elif event == _IRQ_GATTC_WRITE_DONE:
            conn_handle, value_handle, status = data
            if status == 0:
                print(f"書き込み成功: handle={value_handle}")
            else:
                print(f"書き込み失敗: handle={value_handle}, status={status}")

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            print(f"通知受信: {notify_data}")

    def __addr_to_str(self, addr):
        return ':'.join('%02x' % b for b in addr)

    def scan_for_device(self, target_mac, duration_ms=10000):
        """特定のMACアドレスを持つデバイスをスキャン"""
        self._is_target_found = False
        self._target_addr_bytes = None
        self._target_addr_type = None
        target_mac_lower = target_mac.lower()
        
        def scan_callback(addr_type, addr, adv_type, rssi, adv_data):
            addr_str = self.__addr_to_str(addr)
            if addr_str == target_mac_lower:
                print(f"ターゲットデバイス発見: {addr_str}")
                self._is_target_found = True
                self._target_addr_type = addr_type
                self._target_addr_bytes = bytes(addr)
                # ターゲットが見つかったらスキャン停止
                self._ble.gap_scan(None)

        print(f"デバイススキャン開始: {target_mac}")
        self._scan_callback = scan_callback
        self._ble.gap_scan(duration_ms, 30000, 30000)

        # スキャン完了まで待機
        start_time = time.ticks_ms()
        while not self._is_target_found and time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
            time.sleep_ms(100)

        self._ble.gap_scan(None)
        time.sleep_ms(500)
        
        return self._is_target_found

    def connect_to_target(self, timeout_ms=10000):
        """スキャンで見つかったターゲットデバイスに接続"""
        if not self._is_target_found:
            print("ターゲットデバイスが見つかっていません")
            return False

        print(f"接続試行: {self._target_addr_bytes.hex() if self._target_addr_bytes else 'None'}")
        try:
            self._ble.gap_connect(self._target_addr_type, self._target_addr_bytes)
        except Exception as e:
            print(f"接続エラー: {e}")
            return False

        # 接続完了まで待機
        start_time = time.ticks_ms()
        while not self._is_connected and time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            time.sleep_ms(100)

        if self._is_connected:
            return True
        else:
            return False

    def disconnect(self):
        """接続を切断"""
        if self._conn_handle is not None:
            print(f"切断要求送信: handle={self._conn_handle}")
            self._ble.gap_disconnect(self._conn_handle)
            
            # 切断完了まで待機
            start_time = time.ticks_ms()
            while self._is_connected and time.ticks_diff(time.ticks_ms(), start_time) < 5000:
                time.sleep_ms(100)

    def discover_services(self):
        """サービスを検索"""
        if self._conn_handle is not None:
            self._ble.gattc_discover_services(self._conn_handle, self._service_uuid)
            time.sleep(1)

    def discover_characteristics(self, start_handle=None, end_handle=None, uuid=None):
        """Characteristicを検索"""
        if self._conn_handle is not None:
            start = start_handle or self._start_handle or 1
            end = end_handle or self._end_handle or 0xFFFF
            self._ble.gattc_discover_characteristics(self._conn_handle, start, end, uuid)
            time.sleep(1)

    def write_characteristic(self, data, value_handle=None, response=True):
        """Characteristicに書き込み"""
        if self._conn_handle is not None:
            handle = value_handle or self._char_handle
            if handle is not None:
                print(f"データ書き込み: {data.hex()} to handle {handle}")
                self._ble.gattc_write(self._conn_handle, handle, data, 1 if response else 0)
                time.sleep_ms(200)
                return True
            else:
                print("Characteristicハンドルが見つかりません")
        return False

    def is_connected(self):
        """接続状態を確認"""
        return self._is_connected
