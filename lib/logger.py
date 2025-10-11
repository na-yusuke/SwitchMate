"""
Lightweight logging system for MicroPython
省電力かつメモリ効率の良いロギングシステム
"""

import time


class LogLevel:
    """ログレベル定数"""

    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    NONE = 5  # ログを完全に無効化


class Logger:
    """軽量ロガークラス"""

    # クラス変数（全インスタンスで共有）
    _global_level = LogLevel.INFO
    _enabled = True
    _show_timestamp = True
    _show_level = True

    def __init__(self, name):
        """
        ロガーを初期化

        Args:
            name: ロガー名（通常はモジュール名）
        """
        self.name = name

    @classmethod
    def set_level(cls, level):
        """
        グローバルログレベルを設定

        Args:
            level: LogLevel定数
        """
        cls._global_level = level

    @classmethod
    def enable(cls):
        """ロギングを有効化"""
        cls._enabled = True

    @classmethod
    def disable(cls):
        """ロギングを無効化（省電力モード用）"""
        cls._enabled = False

    @classmethod
    def set_timestamp(cls, enabled):
        """タイムスタンプ表示の切り替え"""
        cls._show_timestamp = enabled

    @classmethod
    def set_show_level(cls, enabled):
        """ログレベル表示の切り替え"""
        cls._show_level = enabled

    def _log(self, level, level_name, message):
        """内部ログメソッド"""
        if not self._enabled or level < self._global_level:
            return

        parts = []

        # タイムスタンプ
        if self._show_timestamp:
            timestamp = time.ticks_ms()
            parts.append(f"[{timestamp:010d}]")

        # ログレベル
        if self._show_level:
            parts.append(f"[{level_name}]")

        # ロガー名
        parts.append(f"[{self.name}]")

        # メッセージ
        parts.append(message)

        print(" ".join(parts))

    def debug(self, message):
        """DEBUGレベルのログ"""
        self._log(LogLevel.DEBUG, "DEBUG", message)

    def info(self, message):
        """INFOレベルのログ"""
        self._log(LogLevel.INFO, "INFO", message)

    def warning(self, message):
        """WARNINGレベルのログ"""
        self._log(LogLevel.WARNING, "WARN", message)

    def error(self, message):
        """ERRORレベルのログ"""
        self._log(LogLevel.ERROR, "ERROR", message)

    def critical(self, message):
        """CRITICALレベルのログ"""
        self._log(LogLevel.CRITICAL, "CRIT", message)


# グローバル設定用のヘルパー関数
def set_log_level(level):
    """グローバルログレベルを設定"""
    Logger.set_level(level)


def enable_logging():
    """ロギングを有効化"""
    Logger.enable()


def disable_logging():
    """ロギングを無効化（省電力モード）"""
    Logger.disable()


def configure(level=LogLevel.INFO, timestamp=True, show_level=True):
    """
    ロギングシステムを設定

    Args:
        level: ログレベル
        timestamp: タイムスタンプ表示の有無
        show_level: ログレベル表示の有無
    """
    Logger.set_level(level)
    Logger.set_timestamp(timestamp)
    Logger.set_show_level(show_level)


# ファクトリー関数
def get_logger(name):
    """
    ロガーインスタンスを取得

    Args:
        name: ロガー名（通常は __name__ を渡す）

    Returns:
        Logger: ロガーインスタンス
    """
    return Logger(name)
