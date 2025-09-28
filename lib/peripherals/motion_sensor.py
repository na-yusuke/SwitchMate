from machine import Pin


class MotionSensor:
    def __init__(self, pin):
        self._pir = Pin(pin, Pin.IN)

    def is_motion_detected(self):
        return self._pir.value() == 1
