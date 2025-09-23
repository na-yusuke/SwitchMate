from original_motion_sensor import main as original_motion_sensor
from lib import DeviceAPI
from config import DEBUG

def main():
    """メイン処理"""
    if DEBUG:
        print("Starting SwitchBot API demo...")

    # device_api = DeviceAPI()
    # print("=== Retrieving Device List ===")
    # device_api.print_devices()

    original_motion_sensor.run()


if __name__ == "__main__":
    main()
