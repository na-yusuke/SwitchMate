from infrastructure.ble import BleConnectionPool
from infrastructure.switchbot import ColorBulb
from shared import get_logger

logger = get_logger("ColorBulbManipulator")


class ColorBulbManipulator:
    """Manipulate multiple ColorBulb devices"""

    def __init__(self, bulbs: list[ColorBulb], connection_pool: BleConnectionPool) -> None:
        """
        Initialize ColorBulbManipulator

        Args:
            bulbs: List of ColorBulb instances to manage
            connection_pool: BLE connection pool for managing multiple connections
        """
        self._bulbs: list[ColorBulb] = bulbs
        self._connection_pool: BleConnectionPool = connection_pool

    def connect_all(self) -> bool:
        """
        Connect to all managed bulbs

        Returns:
            bool: True if all connections succeeded
        """
        logger.info(f"Connecting to {len(self._bulbs)} bulbs")
        results = self._connection_pool.connect_all()
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Connected to {success_count}/{len(self._bulbs)} bulbs")
        return success_count == len(self._bulbs)

    def disconnect_all(self) -> None:
        """Disconnect from all managed bulbs"""
        logger.info("Disconnecting from all bulbs")
        self._connection_pool.disconnect_all()

    def power_on_all(self) -> None:
        """Turn on all managed bulbs (assumes already connected)"""
        if not self.connect_all():
            logger.error("Cannot control bulb - connection failed")
            return

        logger.info(f"Power on {len(self._bulbs)} bulbs")
        for bulb in self._bulbs:
            if self._connection_pool.is_connected(bulb.mac_address):
                bulb.power_on()
                logger.debug(f"Powered on {bulb.mac_address}")
            else:
                logger.warning(f"Cannot power on {bulb.mac_address} - not connected")

    def power_off_all(self) -> None:
        """Turn off all managed bulbs (assumes already connected)"""
        if not self.connect_all():
            logger.error("Cannot control bulb - connection failed")
            return

        logger.info(f"Power off {len(self._bulbs)} bulbs")
        for bulb in self._bulbs:
            if self._connection_pool.is_connected(bulb.mac_address):
                bulb.power_off()
                logger.debug(f"Powered off {bulb.mac_address}")
            else:
                logger.warning(f"Cannot power off {bulb.mac_address} - not connected")

    def is_any_powered_on(self) -> bool:
        """
        Check if any bulb is powered on

        Returns:
            bool: True if at least one bulb is powered on
        """
        return any(bulb.is_powered_on() for bulb in self._bulbs)

    def sync_status_all(self, timeout_ms: int = 5000) -> None:
        """
        Sync status for all managed bulbs

        Args:
            timeout_ms: Timeout in milliseconds for each sync operation
        """
        logger.info(f"Syncing status for {len(self._bulbs)} bulbs")
        for bulb in self._bulbs:
            if self._connection_pool.is_connected(bulb.mac_address):
                bulb.sync_status(timeout_ms)
                logger.debug(f"Synced status for {bulb.mac_address}")
            else:
                logger.warning(f"Cannot sync {bulb.mac_address} - not connected")

    def prepare_for_sleep(self) -> None:
        """Prepare all connections for sleep mode"""
        logger.info("Preparing all bulb connections for sleep")
        self._connection_pool.prepare_for_sleep()

    @property
    def bulbs(self) -> list[ColorBulb]:
        return self._bulbs
