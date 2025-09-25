from original_motion_sensor import main as original_motion_sensor
from config import DEBUG

def main():
    """メイン処理"""
    if DEBUG:
        print("Starting SwitchBot API demo...")

    original_motion_sensor.run()


if __name__ == "__main__":
    main()
