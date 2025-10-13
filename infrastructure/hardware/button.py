import time

from machine import Pin

from shared import get_logger

logger = get_logger("Button")


class Button:
    def __init__(self, pin: int) -> None:
        self._button: Pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._is_pressed: bool = False
        self._pressed_callback = None  # Callback function (MicroPython doesn't support Callable type hint)
        self._last_button_state: int = 1

    def set_callback(self, pressed_callback) -> None:
        logger.debug("Setting button callback")
        self._pressed_callback = pressed_callback

    def is_pressed(self) -> bool:
        return self._is_pressed

    def monitor(self) -> None:
        # Read the current button state (LOW=0 means pressed)
        current_button_state = self._button.value()

        # Detect the moment the button is pressed (change from 1 to 0)
        if self._last_button_state == 1 and current_button_state == 0:
            if not self._is_pressed:
                logger.debug("Button pressed")
                self._is_pressed = True
                if self._pressed_callback:
                    self._pressed_callback()
        # Detect the moment the button is released (change from 0 to 1)
        elif self._last_button_state == 0 and current_button_state == 1:
            if self._is_pressed:
                logger.debug("Button released")
                self._is_pressed = False

        # Update the last state
        self._last_button_state = current_button_state
        # Short delay for debouncing
        time.sleep_ms(50)
