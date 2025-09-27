import bluetooth
import time

from config import SWITCHBOT_SERVICE_UUID, SWITCHBOT_CHARACTERISTIC_UUID
from device_config import DEVICE_CONFIG
from lib.ble import BleClient
from lib.switchbot import ColorBulb


def run():
    client = BleClient(bluetooth.UUID(SWITCHBOT_SERVICE_UUID), bluetooth.UUID(SWITCHBOT_CHARACTERISTIC_UUID))
    color_bulb = ColorBulb(client)

    try:
        target_mac = DEVICE_CONFIG["color_bulb"]["desk_light"]["ble_mac_address"]

        # Step 1: デバイススキャン
        if not client.scan_for_device(target_mac, 15000):
            print("ターゲットデバイスが見つかりませんでした")
            return

        # Step 2: 接続
        if not client.connect_to_target(10000):
            print("接続に失敗しました")
            return
        print("接続成功")

        # Step 3: サービス発見
        client.discover_services()
        time.sleep(2)

        # Step 4: Characteristic発見
        client.discover_characteristics()
        time.sleep(2)

        # Step 5: コマンド実行
        if client._char_handle:
            print("SwitchBotCharacteristic発見済み")
            
            # 電源操作テスト
            color_bulb.power_off()
            time.sleep(2)

            color_bulb.power_on()
            time.sleep(2)
        else:
            print("SwitchBotCharacteristicが見つかりません")

        # Step 6: 接続維持
        print("接続を5秒間維持します...")
        time.sleep(5)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
    
    finally:
        # Step 7: 切断
        print("切断処理開始")
        client.disconnect()
        print("処理完了")
