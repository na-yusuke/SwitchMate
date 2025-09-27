from original_motion_sensor import main as original_motion_sensor
from config import DEBUG

import gc


def main():
    """Main processing"""
    if DEBUG:
        print("Starting SwitchBot API demo...")

    gc.collect()
    print("Free memory:", gc.mem_free())

    original_motion_sensor.run()


if __name__ == "__main__":
    main()
