from machine import Pin


class MotionSensor:
    def __init__(self, pin: int) -> None:
        self._pir: Pin = Pin(pin, Pin.IN)

    def is_motion_detected(self) -> bool:
        return self._pir.value() == 1
