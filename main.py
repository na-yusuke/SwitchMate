import gc

from config import DEBUG
from original_motion_sensor import main as original_motion_sensor


def main():
    """Main processing"""
    if DEBUG:
        print("Starting SwitchBot API demo...")

    gc.collect()
    print("Free memory:", gc.mem_free())

    original_motion_sensor.run()


if __name__ == "__main__":
    main()
