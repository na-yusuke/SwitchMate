import time

from machine import Pin


class Button:
    def __init__(self, pin):
        self._button = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._is_pressed = False
        self._pressed_callback = None
        self._last_button_state = 1

    def set_callback(self, _pressed_callback):
        self._pressed_callback = _pressed_callback

    def is_pressed(self):
        return self._is_pressed

    def monitor(self):
        # 現在のボタン状態を読み取り（LOW=0が押下状態）
        current_button_state = self._button.value()

        # ボタンが押された瞬間を検出（1→0の変化）
        if self._last_button_state == 1 and current_button_state == 0:
            if not self._is_pressed:
                print("ボタンが押されました！")
                self._is_pressed = True
                if self._pressed_callback:
                    self._pressed_callback()
        # ボタンが離された瞬間を検出（0→1の変化）
        elif self._last_button_state == 0 and current_button_state == 1:
            if self._is_pressed:
                print("ボタンが離されました")
                self._is_pressed = False

        # 前回の状態を更新
        self._last_button_state = current_button_state
        # チャタリング対策の短い待機
        time.sleep_ms(50)
