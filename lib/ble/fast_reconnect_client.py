"""
Fast BLE reconnection wrapper for BleClient
"""

import time

from lib.ble import BleClient
from lib.logger import get_logger

logger = get_logger("FastReconnect")


class FastReconnectClient:
    """BLE Client wrapper for fast reconnection"""

    def __init__(self, ble_client):
        self._client: BleClient = ble_client

    def connect_with_cache(self, target_mac, scan_timeout_ms=3000, connect_timeout_ms=5000):
        """
        Reconnect to a BLE device using cached address if possible, otherwise scan and connect.

        Args:
            target_mac: target MAC address (string format, e.g. "AA:BB:CC:DD:EE:FF")
            scan_timeout_ms: scan timeout
            connect_timeout_ms: connection timeout

        Returns:
            bool: True if connected, False otherwise
        """
        if self._client.is_connected():
            logger.info("Already connected")
            return True

        if self._client.get_addr_info() != (None, None):
            logger.debug("Trying cached address...")
            if self.__try_direct_connect(connect_timeout_ms):
                logger.info("Connected using cache")
                return True
            else:
                logger.warning("Cache failed, falling back to scan")

        logger.info(f"Scanning for {target_mac}...")
        start_time = time.ticks_ms()

        if not self._client.scan_for_device(target_mac, scan_timeout_ms):
            logger.error("Device not found")
            return False

        if not self._client.connect_to_target(connect_timeout_ms):
            logger.error("Connection failed")
            return False

        logger.debug("Discovering services...")
        self._client.discover_services()

        logger.debug("Discovering characteristics...")
        self._client.discover_characteristics()

        connect_duration = time.ticks_diff(time.ticks_ms(), start_time)
        logger.info(f"Connected in {connect_duration}ms")

        return True

    def __try_direct_connect(self, timeout_ms):
        """Attempt direct connection using cached address"""
        try:
            return self._client.connect_to_target(timeout_ms)
        except Exception as e:
            logger.error(f"Direct connect error: {e}")
            return False

    def is_connected(self):
        """Check connection status"""
        return self._client.is_connected()

    def disconnect(self):
        """Disconnect from the BLE device"""
        self._client.disconnect()

    @property
    def client(self):
        """Access the underlying BleClient instance"""
        return self._client
