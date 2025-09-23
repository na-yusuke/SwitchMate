from machine import Pin


class MotionSensor:
    def __init__(self, pin):
        self.pir = Pin(pin, Pin.IN)

    def is_motion_detected(self):
        return self.pir.value() == 1
