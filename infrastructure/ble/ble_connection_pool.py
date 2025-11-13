import json

from machine import RTC

from infrastructure.ble import BleClient, BleConnectionManager
from shared import get_logger

logger = get_logger("BleConnectionPool")


class BleConnectionPool:
    """BLE Connection Pool for managing multiple simultaneous BLE connections"""

    def __init__(self, service_uuid, characteristic_uuid) -> None:
        """
        Initialize BleConnectionPool

        Args:
            service_uuid: Service UUID for BLE devices
            characteristic_uuid: Characteristic UUID for BLE devices
        """
        self._service_uuid = service_uuid
        self._characteristic_uuid = characteristic_uuid
        self._connections: dict[str, BleConnectionManager] = {}
        self._ble_client: BleClient = BleClient(service_uuid, characteristic_uuid)
        self._rtc: RTC = RTC()

    def add_device(self, target_mac_address: str) -> None:
        """
        Add a device to the connection pool

        Args:
            target_mac_address: MAC address of the device to add
        """
        if target_mac_address in self._connections.keys():
            logger.debug(f"Device {target_mac_address} already in pool")
            return

        # Create dedicated ConnectionManager for this device
        connection_manager = BleConnectionManager(
            target_mac_address, self._ble_client, self._service_uuid, self._characteristic_uuid
        )

        self._connections[target_mac_address] = connection_manager
        logger.info(f"Added device {target_mac_address} to connection pool")

    def connect_all(self) -> dict[str, bool]:
        """
        Connect to all devices in the pool

        Returns:
            dict: Mapping of MAC address to connection success status
        """
        results = {}
        logger.info(f"Connecting to {len(self._connections)} devices")

        for mac_address in self._connections.keys():
            results[mac_address] = self.ensure_connected(mac_address)

        successful = sum(1 for success in results.values() if success)
        logger.info(f"Connected to {successful}/{len(self._connections)} devices")
        return results

    def ensure_connected(self, target_mac_address: str) -> bool:
        """
        Ensure connection to a specific device

        Args:
            target_mac_address: MAC address of the device

        Returns:
            bool: True if connected successfully
        """
        connection_manager = self._connections.get(target_mac_address, {})
        if not connection_manager:
            return False

        return connection_manager.ensure_connected()

    def disconnect_all(self) -> None:
        """Disconnect from all devices"""
        active_connections = self.get_active_connections()
        logger.info(f"Disconnecting from {len(active_connections)} active connections")

        for mac_address in active_connections:
            self.disconnect(mac_address)

    def disconnect(self, target_mac_address: str) -> None:
        """
        Disconnect from a specific device

        Args:
            target_mac_address: MAC address of the device
        """
        if not self.is_connected(target_mac_address):
            logger.info(f"Device {target_mac_address} is already disconnected")
            return

        self._connections.get(target_mac_address).disconnect()
        logger.debug(f"Disconnected from {target_mac_address}")

    def is_connected(self, target_mac_address: str) -> bool:
        """
        Check if connected to a specific device

        Args:
            target_mac_address: MAC address of the device

        Returns:
            bool: True if connected
        """
        connection_manager = self._connections.get(target_mac_address)
        if not connection_manager:
            return False
        return connection_manager.is_connected()

    def get_active_connections(self) -> dict[str, BleConnectionManager]:
        """
        Get dict of currently connected devices

        Returns:
            dict[str, BleConnectionManager]: Dictionary mapping MAC addresses to their connection managers for connected devices only
        """
        return {
            mac: connection_manager
            for mac, connection_manager in self._connections.items()
            if connection_manager.is_connected()
        }

    def prepare_for_sleep(self) -> None:
        """
        Prepare for entering sleep mode

        This method should be called before entering light sleep or deep sleep.
        It will:
        1. Cache the current BLE address to RTC memory for fast reconnection
        2. Disconnect the BLE connection cleanly

        After waking from sleep, call ensure_connected() to reconnect.
        """
        logger.info("Preparing all connections for sleep")
        self.__cache_addr_info()

    def __cache_addr_info(self) -> None:
        """
        Cache BLE connection info to RTC memory for fast reconnection after sleep

        This method:
        1. Collects device connection information from all registered devices
        2. Validates that all required fields are present
        3. Disconnects active connections before sleep
        4. Stores the data in RTC memory as JSON
        """
        try:
            cached_devices = {}

            for connection_manager in self._connections.values():
                # Get device info from BLE client
                device = self._ble_client.devices.get(connection_manager.mac_address)
                if not device:
                    continue

                # Validate all required fields exist
                if not self.__is_device_cacheable(device):
                    logger.debug(f"Skipping device {connection_manager.mac_address}: incomplete data")
                    continue

                # Convert MAC address bytes to string format
                addr_bytes = device["addr_bytes"]
                addr_str = ":".join("%02x" % b for b in addr_bytes)

                # Build cache data structure (FIXED: correct field mapping)
                cached_devices[addr_str] = {
                    "conn_handle": device["conn_handle"],
                    "start_handle": device["start_handle"],
                    "end_handle": device["end_handle"],
                    "char_handle": device["char_handle"],
                    "addr_type": device["addr_type"],
                    "addr_bytes": list(device["addr_bytes"]),
                }

                # Disconnect if currently connected
                if connection_manager.is_connected():
                    logger.info(f"Disconnecting {addr_str} before sleep")
                    connection_manager.disconnect()

            # Save to RTC memory
            if cached_devices:
                cached_json = json.dumps(cached_devices)
                self._rtc.memory(cached_json.encode())
                logger.debug(f"Cached {len(cached_devices)} device(s) to RTC memory")
            else:
                logger.debug("No devices to cache")

        except Exception as e:
            logger.error(f"Failed to cache address info: {e}")

    def __is_device_cacheable(self, device: dict) -> bool:
        """
        Check if device has all required fields for caching

        Args:
            device: Device dictionary from BLE client

        Returns:
            bool: True if device has all required fields
        """
        required_fields = ["conn_handle", "start_handle", "end_handle", "char_handle", "addr_type", "addr_bytes"]
        return all(device.get(field) is not None for field in required_fields)

    def restore_addr_cache(self) -> None:
        """
        Restore BLE connection info from RTC memory after sleep

        This method:
        1. Reads cached device data from RTC memory
        2. Validates each device's required fields
        3. Restores connection information to BLE client

        Call this method after waking from sleep to restore connection info
        without requiring a new device scan.
        """
        try:
            # Read from RTC memory
            mem = self._rtc.memory()
            if not mem:
                logger.debug("No cache found in RTC memory")
                return

            # Parse JSON data
            cached_devices = json.loads(mem.decode())
            logger.debug(f"Found {len(cached_devices)} cached device(s)")

            # Restore each device
            restored_count = 0
            for mac_address, device_data in cached_devices.items():
                if self.__restore_single_device(mac_address, device_data):
                    restored_count += 1

            logger.info(f"Restored {restored_count}/{len(cached_devices)} device(s) from RTC memory")

        except Exception as e:
            logger.error(f"Failed to restore address info: {e}")

    def __restore_single_device(self, mac_address: str, device_data: dict) -> bool:
        """
        Restore a single device from cached data

        Args:
            mac_address: MAC address of the device
            device_data: Cached device data dictionary

        Returns:
            bool: True if device was successfully restored
        """
        # Validate required fields
        if not self.__is_device_cacheable(device_data):
            logger.warning(f"Skipping {mac_address}: incomplete cached data")
            return False

        # Build restore data (FIXED: correct field mapping)
        restore_data = {
            "conn_handle": device_data["conn_handle"],
            "start_handle": device_data["start_handle"],
            "end_handle": device_data["end_handle"],
            "char_handle": device_data["char_handle"],
            "addr_type": device_data["addr_type"],
            "addr_bytes": bytes(device_data["addr_bytes"]),
        }

        # Restore to BLE client
        if self._ble_client.restore_addr_info(mac_address, restore_data):
            logger.info(f"Restored device: {mac_address}")
            return True
        else:
            logger.warning(f"Failed to restore device: {mac_address}")
            return False

    @property
    def ble_client(self) -> BleClient:
        return self._ble_client
