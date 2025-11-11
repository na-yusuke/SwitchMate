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

    def get_client(self) -> BleClient | None:
        """
        Get BleClient

        Returns:
            BleClient instance
        """
        return self._ble_client

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

    def disconnect_all(self) -> None:
        """Disconnect from all devices"""
        active_connections = self.get_active_connections()
        logger.info(f"Disconnecting from {len(active_connections)} active connections")

        for mac_address in active_connections:
            self.disconnect(mac_address)

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
        Prepare all connections for sleep mode

        Caches connection info and disconnects all devices
        """
        logger.info("Preparing all connections for sleep")

        for connection_manager in self._connections.values():
            connection_manager.prepare_for_sleep()
