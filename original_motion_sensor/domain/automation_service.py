import time


class BulbAutomationService:
    """
    Business logic for automatic bulb control
    """

    def __init__(self, power_on_duration_ms: int, check_status_duration_ms: int) -> None:
        """
        Initialize automation service

        Args:
            power_on_duration_ms: Duration to keep bulb on (milliseconds)
        """
        self._power_on_duration_ms: int = power_on_duration_ms
        self._last_power_on_time: int = self.__get_distant_future()
        self._check_status_duration_ms: int = check_status_duration_ms
        self._last_check_status_time: int = self.__get_distant_future()

    @staticmethod
    def __get_distant_future() -> int:
        """Get a timestamp far in the future"""
        return time.ticks_add(0, -1) // 2 - 1

    def should_power_off_bulb(self) -> bool:
        """
        Check if bulb should be turned off

        Returns:
            bool: True if enough time has elapsed
        """
        # Business rule: Turn off after duration elapsed
        elapsed = time.ticks_diff(time.ticks_ms(), self._last_power_on_time)
        return elapsed > self._power_on_duration_ms

    def should_get_bulb_status(self) -> bool:
        """
        Check if bulb status should be fetched

        Returns:
            bool: True if enough time has elapsed
        """
        elapsed = time.ticks_diff(time.ticks_ms(), self._last_check_status_time)
        return elapsed > self._check_status_duration_ms

    def record_last_power_on_time(self) -> None:
        """Record the last power on time"""
        self._last_power_on_time = time.ticks_ms()

    def reset_power_on_time(self) -> None:
        """Reset power on time to distant past"""
        self._last_power_on_time = self.__get_distant_future()

    def record_last_check_status_time(self) -> None:
        """Record the last check status time"""
        self._last_check_status_time = time.ticks_ms()
