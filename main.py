from switchbot import DeviceAPI
from config import DEBUG

def main():
    """メイン処理"""
    if DEBUG:
        print("Starting SwitchBot API demo...")

    device_api = DeviceAPI()
    print("=== Retrieving Device List ===")
    device_api.print_devices()


if __name__ == "__main__":
    main()
