import time

import ubluetooth
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
    def __init__(self, service_uuid: ubluetooth.UUID, characteristic_uuid: ubluetooth.UUID) -> None:
        self._ble: ubluetooth.BLE = ubluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self.__irq)
        self.__reset()

        self._service_uuid: ubluetooth.UUID = service_uuid
        self._characteristic_uuid: ubluetooth.UUID = characteristic_uuid

    def __reset(self) -> None:
        # Device states - keyed by MAC address
        # Each entry contains all state information for a device
        self._devices: dict[str, dict] = {}
        # Structure: {
        #   "aa:bb:cc:dd:ee:ff": {
        #     "conn_handle": int | None,
        #     "start_handle": int | None,
        #     "end_handle": int | None,
        #     "char_handle": int | None,
        #     "notify_handle": int | None,
        #     "is_found": bool,
        #     "is_connected": bool,
        #     "service_discovery_done": bool,
        #     "characteristic_discovery_done": bool,
        #     "addr_type": int | None,
        #     "addr_bytes": bytes | None,
        #     "adv_data": bytes | None,
        #     "last_notification": bytes | None
        #   }
        # }

        # Scan state
        self._scan_callback = None
        # Notification callback
        self._notification_callback = None

    def __irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            mac_address = self.__addr_to_str(addr)
            logger.debug(f"Device discovered: {mac_address}, RSSI: {rssi}")

            if self._scan_callback:
                self._scan_callback(addr_type, addr, adv_type, rssi, adv_data)

        elif event == _IRQ_SCAN_DONE:
            logger.debug("Scan completed")

        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            mac_address = self.__addr_to_str(addr)
            logger.info(f"Connected: {mac_address}")

            # Initialize device if not exists
            self.__init_device(mac_address)

            # Update connection state
            self._devices[mac_address]["conn_handle"] = conn_handle
            self._devices[mac_address]["is_connected"] = True
            self._devices[mac_address]["addr_type"] = addr_type
            self._devices[mac_address]["addr_bytes"] = bytes(addr)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            mac_address = self.__addr_to_str(addr)
            logger.info(f"Disconnected: {mac_address}")

            if mac_address in self._devices.keys():
                self._devices[mac_address]["is_connected"] = False

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            logger.debug(f"Service discovered: {uuid}")
            if uuid == self._service_uuid:
                mac_address = self.__get_mac_by_handle(conn_handle)
                if mac_address and mac_address in self._devices:
                    self._devices[mac_address]["start_handle"] = start_handle
                    self._devices[mac_address]["end_handle"] = end_handle
                    logger.info(f"Target service found for {mac_address}: {start_handle}-{end_handle}")

        elif event == _IRQ_GATTC_SERVICE_DONE:
            conn_handle, status = data
            logger.debug(f"Service discovery done: status={status}")
            mac_address = self.__get_mac_by_handle(conn_handle)
            if mac_address and mac_address in self._devices.keys():
                self._devices[mac_address]["service_discovery_done"] = True

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            logger.debug(f"Characteristic: {uuid}, handle={value_handle}")
            if uuid == self._characteristic_uuid:
                mac_address = self.__get_mac_by_handle(conn_handle)
                if mac_address and mac_address in self._devices.keys():
                    self._devices[mac_address]["char_handle"] = value_handle
                    logger.info(f"Target characteristic found for {mac_address}: handle={value_handle}")

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            conn_handle, status = data
            logger.debug(f"Characteristic discovery done: status={status}")
            mac_address = self.__get_mac_by_handle(conn_handle)
            if mac_address and mac_address in self._devices.keys():
                self._devices[mac_address]["characteristic_discovery_done"] = True

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
            mac_address = self.__get_mac_by_handle(conn_handle)
            if mac_address and mac_address in self._devices.keys():
                try:
                    # Create a proper copy of the data to preserve it outside IRQ context
                    data_copy = bytearray(notify_data)
                    logger.debug(f"Notification from {mac_address}: {data_copy.hex()}")
                    self._devices[mac_address]["last_notification"] = bytes(data_copy)
                    if self._notification_callback:
                        self._notification_callback(bytes(data_copy))
                except Exception as e:
                    logger.error(f"Notification error: {e}")
                    self._devices[mac_address]["last_notification"] = None

    def __addr_to_str(self, addr: bytes) -> str:
        return ":".join("%02x" % b for b in addr)

    def __get_mac_by_handle(self, conn_handle: int) -> str | None:
        """Get MAC address by connection handle"""
        return next(
            (mac_address for mac_address, device in self._devices.items() if device.get("conn_handle") == conn_handle),
            None,
        )

    def __init_device(self, target_mac_address: str) -> None:
        """Initialize device entry in dictionary"""
        self._devices.setdefault(
            target_mac_address,
            {
                "conn_handle": None,
                "start_handle": None,
                "end_handle": None,
                "char_handle": None,
                "notify_handle": None,
                "is_found": False,
                "is_connected": False,
                "service_discovery_done": False,
                "characteristic_discovery_done": False,
                "addr_type": None,
                "addr_bytes": None,
                "adv_data": None,
                "last_notification": None,
            },
        )

    def scan_for_device(self, target_mac_address: str, duration_ms: int = 10000) -> bool:
        """Scan for device with specific MAC address"""
        target_mac_address_lower = target_mac_address.lower()
        self.__init_device(target_mac_address_lower)

        def scan_callback(addr_type, addr, adv_type, rssi, adv_data):
            mac_address = self.__addr_to_str(addr)
            if mac_address == target_mac_address_lower:
                logger.info(f"Target device found: {mac_address}")
                self._devices[mac_address]["is_found"] = True
                self._devices[mac_address]["addr_type"] = addr_type
                self._devices[mac_address]["addr_bytes"] = bytes(addr)
                self._devices[mac_address]["adv_data"] = adv_data
                # Stop scanning when target is found
                self._ble.gap_scan(None)

        logger.info(f"Scanning for: {target_mac_address}")
        self._scan_callback = scan_callback
        self._ble.gap_scan(duration_ms, 30000, 30000)

        # Wait for scan completion
        start_time = time.ticks_ms()
        while (
            not self._devices.get(target_mac_address, {}).get("is_found")
            and time.ticks_diff(time.ticks_ms(), start_time) < duration_ms
        ):
            time.sleep_ms(100)

        self._ble.gap_scan(None)

        return self._devices.get(target_mac_address, {}).get("is_found")

    def connect_to_target(self, target_mac_address: str, timeout_ms: int = 10000) -> bool:
        """Connect to target device found in scan"""
        device = self._devices.get(target_mac_address, {})
        if not device:
            logger.error("Device info not found")
            return False

        addr_bytes = device.get("addr_bytes")
        addr_type = device.get("addr_type")

        logger.info(f"Connecting to: {addr_bytes.hex() if addr_bytes else 'None'}")
        try:
            self._ble.gap_connect(addr_type, addr_bytes)
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

        # Wait for connection completion
        start_time = time.ticks_ms()
        while not device.get("is_connected", False) and time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            time.sleep_ms(100)

        return device.get("is_connected", False)

    def disconnect(self, target_mac_address: str, timeout_ms: int = 5000) -> None:
        """Disconnect connection"""
        device = self._devices.get(target_mac_address, {})
        if not device:
            return

        conn_handle = device.get("conn_handle")
        if conn_handle is None:
            return

        logger.info(f"Disconnecting {target_mac_address}: handle={conn_handle}")
        self._ble.gap_disconnect(conn_handle)
        # Wait for disconnection completion
        start_time = time.ticks_ms()
        while device.get("is_connected", False) and time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            time.sleep_ms(100)
        device["is_connected"] = False

    def discover_services(self, target_mac_address: str, timeout_ms: int = 5000) -> bool:
        """
        Discover services and wait for completion

        Args:
            target_mac_address: MAC address of the target device
            timeout_ms: Timeout in milliseconds

        Returns:
            bool: True if discovery completed successfully
        """
        device = self._devices.get(target_mac_address, False)
        if not device:
            return False

        # Reset flag before starting
        device["service_discovery_done"] = False

        conn_handle = device.get("conn_handle")
        if conn_handle is None:
            return False

        self._ble.gattc_discover_services(conn_handle, self._service_uuid)
        # Wait for discovery completion
        start_time = time.ticks_ms()
        while not device.get("service_discovery_done", False):
            if time.ticks_diff(time.ticks_ms(), start_time) >= timeout_ms:
                logger.error(f"Service discovery timeout for {target_mac_address}")
                return False
            time.sleep_ms(100)

        logger.debug(f"Service discovery completed for {target_mac_address}")
        return True

    def discover_characteristics(
        self,
        target_mac_address: str,
        start_handle: int | None = None,
        end_handle: int | None = None,
        uuid: ubluetooth.UUID | None = None,
        timeout_ms: int = 5000,
    ) -> bool:
        """
        Discover characteristics and wait for completion

        Args:
            target_mac_address: MAC address of the target device
            start_handle: Start handle for discovery
            end_handle: End handle for discovery
            uuid: UUID to filter characteristics
            timeout_ms: Timeout in milliseconds

        Returns:
            bool: True if discovery completed successfully
        """
        device = self._devices.get(target_mac_address, False)
        if not device:
            return False

        # Reset flag before starting
        device["characteristic_discovery_done"] = False

        conn_handle = device.get("conn_handle")
        if conn_handle is None:
            return False

        start = start_handle or device.get("start_handle") or 1
        end = end_handle or device.get("end_handle") or 0xFFFF
        self._ble.gattc_discover_characteristics(conn_handle, start, end, uuid)

        # Wait for discovery completion
        start_time = time.ticks_ms()
        while not device.get("characteristic_discovery_done", False):
            if time.ticks_diff(time.ticks_ms(), start_time) >= timeout_ms:
                logger.error(f"Characteristic discovery timeout for {target_mac_address}")
                return False
            time.sleep_ms(100)

        logger.debug(f"Characteristic discovery completed for {target_mac_address}")
        return True

    def write_characteristic(
        self, target_mac_address: str, data: bytes, value_handle: int | None = None, response: bool = True
    ) -> bool:
        """
        Write data to a BLE characteristic

        Args:
            target_mac_address: MAC address of the target device to write to the characteristic
            data: Binary data to write to the characteristic
            value_handle: Characteristic value handle (uses cached handle if None)
            response: Whether to request write response from device

        Returns:
            bool: True if write was successful, False otherwise
        """
        device = self._devices.get(target_mac_address, {})
        if not device:
            return False

        conn_handle = device.get("conn_handle")
        if conn_handle is None:
            return False

        handle = value_handle or device.get("char_handle")
        if handle is None:
            logger.error("Characteristic handle not found")
            return False

        logger.debug(f"Writing: {data.hex()} to handle {handle}")
        self._ble.gattc_write(conn_handle, handle, data, 1 if response else 0)
        return True

    def is_connected(self, target_mac_address: str) -> bool:
        """
        Check if device is currently connected

        Args:
            target_mac_address: MAC address of the target device

        Returns:
            bool: True if device is connected, False otherwise
        """
        return self._devices.get(target_mac_address, {}).get("is_connected", False)

    def get_addr_info(self, target_mac_address: str) -> tuple[int | None, str | None]:
        """
        Get BLE address information of the target device

        Args:
            target_mac_address: MAC address of the target device

        Returns:
            tuple[int | None, str | None]: Tuple of (address_type, address_string).
                                           Returns (None, None) if device not found or address not available
        """
        device = self._devices.get(target_mac_address, {})
        if not device:
            return (None, None)

        addr_bytes = device.get("addr_bytes")
        addr_type = device.get("addr_type")
        if addr_bytes is None:
            return (None, None)
        return addr_type, self.__addr_to_str(addr_bytes)

    def restore_addr_info(self, mac_address: str, restore_data: dict) -> bool:
        """
        Restore device connection information from cached data

        This method is used to restore connection information after sleep/wake cycles
        without requiring a new device scan.

        Args:
            restore_data: Dictionary containing device restoration data with keys:
                - addr_bytes (str): MAC address string in format "aabbccddeeff"
                - addr_type (int): BLE address type (0 for public, 1 for random)
                - conn_handle (int): Connection handle
                - start_handle (int): Service start handle
                - end_handle (int): Service end handle
                - char_handle (int): Characteristic handle

        Returns:
            bool: True if address was successfully restored, False if invalid data or error occurred
        """
        try:
            addr_bytes = restore_data.get("addr_bytes")
            if not addr_bytes or len(addr_bytes) != 6:
                logger.error(f"Invalid address format: expected 6 bytes, got {len(addr_bytes) if addr_bytes else 0}")
                return False

            # Initialize device entry
            self.__init_device(mac_address)

            # Restore device state
            device = self._devices[mac_address]
            device["conn_handle"] = restore_data.get("conn_handle")
            device["start_handle"] = restore_data.get("start_handle")
            device["end_handle"] = restore_data.get("end_handle")
            device["char_handle"] = restore_data.get("char_handle")
            device["addr_type"] = restore_data.get("addr_type")
            device["addr_bytes"] = addr_bytes
            device["is_found"] = True

            logger.info(f"Restored device: {mac_address}")
            return True

        except ValueError as e:
            logger.error(f"Invalid MAC address format: {e}")
            return False
        except Exception as e:
            logger.error(f"Error restoring address: {e}")
            return False

    def get_target_data(self, target_mac_address: str) -> bytes | None:
        """
        Get advertisement data received from target device during scan

        Args:
            target_mac_address: MAC address of the target device

        Returns:
            bytes | None: Raw advertisement data bytes, or None if device not found or no data available
        """
        return self._devices.get(target_mac_address, {}).get("adv_data")

    def set_notification_callback(self, callback) -> None:
        """
        Set callback function to handle BLE notifications from devices

        Args:
            callback: Callback function that takes notification data (bytes) as argument.
                     Called when notification is received from any connected device
        """
        self._notification_callback = callback

    def get_last_notification(self, target_mac_address: str) -> bytes | None:
        """
        Get the most recently received notification data from device

        Args:
            target_mac_address: MAC address of the target device

        Returns:
            bytes | None: Last notification data bytes, or None if no notification received or device not found
        """
        return self._devices.get(target_mac_address, {}).get("last_notification")

    def wait_for_notification(self, target_mac_address: str, timeout_ms: int = 5000) -> bytes | None:
        """
        Wait for notification from device with timeout

        Blocks until a notification is received or timeout expires.

        Args:
            target_mac_address: MAC address of the target device
            timeout_ms: Maximum time to wait in milliseconds (default: 5000ms)

        Returns:
            bytes | None: Notification data if received within timeout, None if timeout or device not found
        """
        logger.debug(f"Waiting for notification (timeout: {timeout_ms}ms)")
        start_time = time.ticks_ms()

        device = self._devices.get(target_mac_address, {})
        if not device:
            return None

        while device.get("last_notification") is None and time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            time.sleep_ms(100)

        notification = device.get("last_notification")
        if notification is None:
            logger.warning("Notification timeout")
            return None
        logger.info(f"Notification received: {len(notification)} bytes")
        return notification

    @property
    def devices(self) -> dict:
        return self._devices
