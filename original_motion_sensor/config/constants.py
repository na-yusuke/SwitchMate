# ---------- Time ----------
# All time values are in milliseconds

seconds = 1000
minutes = 60 * seconds
hours = 60 * minutes

POWER_ON_DURATION = 5 * seconds
COLOR_BULB_CHECK_INTERVAL = 10 * seconds

LIGHT_SLEEP_DURATION = 5 * seconds
LIGHT_SLEEP_THRESHOLD = 8 * seconds
DEEP_SLEEP_THRESHOLD = 30 * minutes

# ---------- Device ----------

MICROCONTROLLER_PIN_CONFIG = {"button": 25, "motion_sensor": 27}

TARGET_COLOR_BULBS = ["corridor_light", "entrance_light"]
