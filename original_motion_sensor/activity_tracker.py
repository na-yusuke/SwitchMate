"""
Activity tracking for sleep management
"""

import time


class ActivityTracker:
    """
    Track user activity for sleep mode decisions
    """

    def __init__(self, light_sleep_threshold_ms: int, deep_sleep_threshold_ms: int) -> None:
        self._light_sleep_threshold: int = light_sleep_threshold_ms
        self._deep_sleep_threshold: int = deep_sleep_threshold_ms
        self._last_activity_time: int = self.__get_distant_future()

    @staticmethod
    def __get_distant_future() -> int:
        """Get a timestamp far in the future"""
        return time.ticks_add(0, -1) // 2 - 1

    def record_activity(self) -> None:
        """Record that activity occurred"""
        self._last_activity_time = time.ticks_ms()

    def get_elapsed_time_from_last_activity(self) -> int:
        """Get the elapsed time from last activity in milliseconds"""
        return time.ticks_diff(time.ticks_ms(), self._last_activity_time)

    def should_enter_light_sleep(self) -> bool:
        """Check if should enter light sleep"""
        return self.get_elapsed_time_from_last_activity() > self._light_sleep_threshold

    def should_enter_deep_sleep(self) -> bool:
        """Check if should enter deep sleep"""
        return self.get_elapsed_time_from_last_activity() > self._deep_sleep_threshold
