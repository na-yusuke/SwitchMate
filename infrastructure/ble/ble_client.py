import time

import bluetooth
from micropython import const

from shared import get_logger

logger = get_logger("BleClient")

# BLE constants
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
    def __init__(self, service_uuid: bluetooth.UUID, characteristic_uuid: bluetooth.UUID) -> None:
        self._ble: bluetooth.BLE = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self.__irq)
        self.__reset()

        self._service_uuid: bluetooth.UUID = service_uuid
        self._characteristic_uuid: bluetooth.UUID = characteristic_uuid

    def __reset(self) -> None:
        # Connection state
        self._conn_handle: int | None = None
        self._is_connected: bool = False

        # GATT handles
        self._start_handle: int | None = None
        self._end_handle: int | None = None
        self._char_handle: int | None = None
        self._notify_handle: int | None = None

        # Scan state
        self._scan_callback = None
        self._is_target_found: bool = False
        self._target_addr_type: int | None = None
        self._target_addr_bytes: bytes | None = None
        self._target_data: bytes | None = None

        # Notification state
        self._notification_callback = None
        self._last_notification_data: bytes | None = None

    def __irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            addr_str = self.__addr_to_str(addr)
            logger.debug(f"Device discovered: {addr_str}, RSSI: {rssi}")

            if self._scan_callback:
                self._scan_callback(addr_type, addr, adv_type, rssi, adv_data)

        elif event == _IRQ_SCAN_DONE:
            logger.debug("Scan completed")

        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            logger.info(f"Connected: {self.__addr_to_str(addr)}")
            self._conn_handle = conn_handle
            self._is_connected = True

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            logger.info(f"Disconnected: {self.__addr_to_str(addr)}")
            self._conn_handle = None
            self._is_connected = False

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            logger.debug(f"Service discovered: {uuid}")
            if uuid == self._service_uuid:
                self._start_handle = start_handle
                self._end_handle = end_handle
                logger.info(f"Target service found: {start_handle}-{end_handle}")

        elif event == _IRQ_GATTC_SERVICE_DONE:
            conn_handle, status = data
            logger.debug(f"Service discovery done: status={status}")

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            logger.debug(f"Characteristic: {uuid}, handle={value_handle}")
            if uuid == self._characteristic_uuid:
                self._char_handle = value_handle
                logger.info(f"Target characteristic found: handle={value_handle}")

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            conn_handle, status = data
            logger.debug(f"Characteristic discovery done: status={status}")

        elif event == _IRQ_GATTC_READ_RESULT:
            conn_handle, value_handle, char_data = data
            logger.debug(f"Read result: {char_data}")

        elif event == _IRQ_GATTC_READ_DONE:
            conn_handle, value_handle, status = data
            logger.debug(f"Read done: status={status}")

        elif event == _IRQ_GATTC_WRITE_DONE:
            conn_handle, value_handle, status = data
            if status == 0:
                logger.debug(f"Write OK: handle={value_handle}")
            else:
                logger.error(f"Write failed: handle={value_handle}, status={status}")

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            self._last_notification_data = None
            try:
                # Create a proper copy of the data to preserve it outside IRQ context
                data_copy = bytearray(notify_data)
                logger.debug(f"Notification: {data_copy.hex()}")
                self._last_notification_data = bytes(data_copy)
                if self._notification_callback:
                    self._notification_callback(bytes(data_copy))
            except Exception as e:
                logger.error(f"Notification error: {e}")
                self._last_notification_data = None

    def __addr_to_str(self, addr: bytes) -> str:
        return ":".join("%02x" % b for b in addr)

    def scan_for_device(self, target_mac: str, duration_ms: int = 10000) -> bool:
        """Scan for device with specific MAC address"""
        self._is_target_found = False
        self._target_addr_bytes = None
        self._target_addr_type = None
        self._target_data = None
        target_mac_lower = target_mac.lower()

        def scan_callback(addr_type, addr, adv_type, rssi, adv_data):
            addr_str = self.__addr_to_str(addr)
            if addr_str == target_mac_lower:
                logger.info(f"Target device found: {addr_str}")
                self._is_target_found = True
                self._target_addr_type = addr_type
                self._target_addr_bytes = bytes(addr)
                self._target_data = adv_data
                # Stop scanning when target is found
                self._ble.gap_scan(None)

        logger.info(f"Scanning for: {target_mac}")
        self._scan_callback = scan_callback
        self._ble.gap_scan(duration_ms, 30000, 30000)

        # Wait for scan completion
        start_time = time.ticks_ms()
        while not self._is_target_found and time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
            time.sleep_ms(100)

        self._ble.gap_scan(None)

        return self._is_target_found

    def connect_to_target(self, timeout_ms: int = 10000) -> bool:
        """Connect to target device found in scan"""
        if not self._is_target_found:
            logger.warning("Target device not found")
            return False

        logger.info(f"Connecting to: {self._target_addr_bytes.hex() if self._target_addr_bytes else 'None'}")
        try:
            self._ble.gap_connect(self._target_addr_type, self._target_addr_bytes)
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

        # Wait for connection completion
        start_time = time.ticks_ms()
        while not self._is_connected and time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            time.sleep_ms(100)

        return self._is_connected

    def disconnect(self, timeout_ms: int = 5000) -> None:
        """Disconnect connection"""
        if self._conn_handle is not None:
            logger.info(f"Disconnecting: handle={self._conn_handle}")
            self._ble.gap_disconnect(self._conn_handle)

            # Wait for disconnection completion
            start_time = time.ticks_ms()
            while self._is_connected and time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
                time.sleep_ms(100)
            self._is_connected = False

    def discover_services(self) -> None:
        """Discover services"""
        if self._conn_handle is not None:
            self._ble.gattc_discover_services(self._conn_handle, self._service_uuid)
            time.sleep(1)

    def discover_characteristics(
        self, start_handle: int | None = None, end_handle: int | None = None, uuid: bluetooth.UUID | None = None
    ) -> None:
        """Discover characteristics"""
        if self._conn_handle is not None:
            start = start_handle or self._start_handle or 1
            end = end_handle or self._end_handle or 0xFFFF
            self._ble.gattc_discover_characteristics(self._conn_handle, start, end, uuid)
            time.sleep(1)

    def write_characteristic(self, data: bytes, value_handle: int | None = None, response: bool = True) -> bool:
        """Write to characteristic"""
        if self._conn_handle is not None:
            handle = value_handle or self._char_handle
            if handle is not None:
                logger.debug(f"Writing: {data.hex()} to handle {handle}")
                self._ble.gattc_write(self._conn_handle, handle, data, 1 if response else 0)
                time.sleep_ms(200)
                return True
            else:
                logger.error("Characteristic handle not found")
        return False

    def is_connected(self) -> bool:
        """Check connection status"""
        return self._is_connected

    def get_addr_info(self) -> tuple[int | None, str | None]:
        """Get address info of the target device"""
        if self._target_addr_bytes is not None:
            return self._target_addr_type, self.__addr_to_str(self._target_addr_bytes)
        return (None, None)

    def restore_addr_info(self, addr_type: int, addr_str: str) -> bool:
        """Restore address info from string and type"""
        try:
            addr_bytes = bytes(int(b, 16) for b in addr_str.split(":"))
            if len(addr_bytes) == 6:
                self._target_addr_type = addr_type
                self._target_addr_bytes = addr_bytes
                self._is_target_found = True
                logger.info(f"Restored address: {addr_str}, type: {addr_type}")
                return True
            else:
                logger.error("Invalid address format")
        except Exception as e:
            logger.error(f"Error restoring address: {e}")
        return False

    def get_target_data(self) -> bytes | None:
        """Get advertisement data of the target device"""
        return self._target_data

    def set_notification_callback(self, callback) -> None:
        """Set callback function for notifications"""
        self._notification_callback = callback

    def get_last_notification(self) -> bytes | None:
        """Get last received notification data"""
        return self._last_notification_data

    def wait_for_notification(self, timeout_ms: int = 5000) -> bytes | None:
        """Wait for notification and return the data"""
        logger.debug(f"Waiting for notification (timeout: {timeout_ms}ms)")
        start_time = time.ticks_ms()

        while self._last_notification_data is None and time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            time.sleep_ms(100)

        if self._last_notification_data is not None:
            logger.info(f"Notification received: {len(self._last_notification_data)} bytes")
            return self._last_notification_data
        else:
            logger.warning("Notification timeout")
            return None
