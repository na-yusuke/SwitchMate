import json
import time

from machine import RTC

from infrastructure.ble import BleClient
from shared import get_logger

logger = get_logger("BleConnectionManager")


class BleConnectionManager:
    """BLE Client wrapper for fast reconnection and lifecycle management"""

    def __init__(self, mac_address: str, ble_client: BleClient, service_uuid: str, characteristic_uuid: str) -> None:
        """
        Initialize BleConnectionManager

        Args:
            ble_client: BleClient instance
        """
        self._mac_address: str = mac_address
        self._client: BleClient = ble_client
        self._rtc: RTC = RTC()

    def disconnect_current(self) -> None:
        """Disconnect from current device to save power"""
        if self._client.is_connected(self._mac_address):
            logger.debug(f"Disconnecting from {self._mac_address}")
            self._client.disconnect(self._mac_address)

    def ensure_connected(self) -> bool:
        """
        Ensure BLE connection is established and healthy

        This is the main method to use for connection management. It will:
        1. Return True if already connected
        2. Restore cached address from RTC memory if available
        3. Attempt connection with retry logic
        4. Fall back to scanning if cache fails

        Returns:
            bool: True if connected successfully
        """
        if not self._mac_address:
            logger.error("Target MAC address not set")
            return False

        # Already connected? Return immediately
        if self._client.is_connected(self._mac_address):
            logger.debug("Already connected")
            return True

        # Restore cached address from RTC memory
        self.__restore_addr_cache()

        # Attempt connection with retry
        return self.__connect_with_retry()

    def __connect_with_retry(
        self, max_retries: int = 5, scan_timeout_ms: int = 3000, connect_timeout_ms: int = 5000
    ) -> bool:
        """
        Attempt connection with retry logic

        Args:
            max_retries: Maximum number of retry attempts
            scan_timeout_ms: Scan timeout in milliseconds
            connect_timeout_ms: Connection timeout in milliseconds

        Returns:
            bool: True if connection succeeded
        """
        for attempt in range(1, max_retries + 1):
            logger.info(f"Connection attempt {attempt}/{max_retries} to {self._mac_address}")

            try:
                if self.__connect_with_cache(scan_timeout_ms, connect_timeout_ms):
                    logger.info(f"Connected successfully on attempt {attempt}")
                    return True
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")

            if attempt < max_retries:
                time.sleep_ms(1000)  # Wait 1 second before retry

        logger.error("All connection attempts failed")
        return False

    def __connect_with_cache(self, scan_timeout_ms: int = 3000, connect_timeout_ms: int = 5000) -> bool:
        """
        Reconnect to a BLE device using cached address if possible, otherwise scan and connect.

        Args:
            scan_timeout_ms: Scan timeout in milliseconds
            connect_timeout_ms: Connection timeout in milliseconds

        Returns:
            bool: True if connected, False otherwise
        """
        if self._client.is_connected(self._mac_address):
            logger.info("Already connected")
            return True

        if self._client.get_addr_info(self._mac_address) != (None, None):
            logger.debug("Trying cached address...")
            if self.__try_direct_connect(connect_timeout_ms):
                logger.info("Connected using cache")
                return True
            else:
                logger.warning("Cache failed, falling back to scan")

        logger.info(f"Scanning for {self._mac_address}...")
        start_time = time.ticks_ms()

        if not self._client.scan_for_device(self._mac_address, scan_timeout_ms):
            logger.error("Device not found")
            return False

        if not self._client.connect_to_target(self._mac_address, connect_timeout_ms):
            logger.error("Connection failed")
            return False

        logger.debug("Discovering services...")
        if not self._client.discover_services(self._mac_address):
            return False

        logger.debug("Discovering characteristics...")
        if not self._client.discover_characteristics(self._mac_address):
            return False

        connect_duration = time.ticks_diff(time.ticks_ms(), start_time)
        logger.info(f"Connected in {connect_duration}ms")

        return True

    def prepare_for_sleep(self) -> None:
        """
        Prepare for entering sleep mode

        This method should be called before entering light sleep or deep sleep.
        It will:
        1. Cache the current BLE address to RTC memory for fast reconnection
        2. Disconnect the BLE connection cleanly

        After waking from sleep, call ensure_connected() to reconnect.
        """
        # Cache address info to RTC memory first
        self.__cache_addr_info()

        # Then disconnect
        if self._client.is_connected(self._mac_address):
            logger.info("Disconnecting BLE before sleep")
            self._client.disconnect(self._mac_address)

    def __cache_addr_info(self) -> None:
        """Cache BLE address info to RTC memory for fast reconnection"""
        try:
            addr_type, addr_str = self._client.get_addr_info(self._mac_address)
            if addr_type is not None and addr_str is not None:
                data = json.dumps({"addr_type": addr_type, "addr_bytes": addr_str})
                self._rtc.memory(data.encode())
                logger.debug("Cached BLE address info to RTC memory")
        except Exception as e:
            logger.error(f"Failed to cache address info: {e}")

    def __restore_addr_cache(self) -> None:
        """Restore BLE address info from RTC memory"""
        try:
            mem = self._rtc.memory()
            if not mem:
                return

            data = json.loads(mem.decode())
            addr_type = data.get("addr_type")
            addr_bytes = data.get("addr_bytes")

            if addr_type is not None and addr_bytes is not None:
                self._client.restore_addr_info(addr_type, addr_bytes)
                logger.info("Restored BLE address info from RTC memory")
        except Exception as e:
            logger.error(f"Failed to restore address info: {e}")

    def __try_direct_connect(self, timeout_ms: int) -> bool:
        """Attempt direct connection using cached address"""
        try:
            return self._client.connect_to_target(self._mac_address, timeout_ms)
        except Exception as e:
            logger.error(f"Direct connect error: {e}")
            return False

    def is_connected(self) -> bool:
        """Check connection status"""
        return self._client.is_connected(self._mac_address)

    def disconnect(self) -> None:
        """Disconnect from the BLE device"""
        self._client.disconnect(self._mac_address)

    @property
    def client(self) -> BleClient:
        """Access the underlying BleClient instance"""
        return self._client
