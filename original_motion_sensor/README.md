# Original Motion Sensor

Original motion sensor that collaborates with [SwitchBot color bulb](https://www.switchbot.jp/products/switchbot-color-bulb?currency=JPY&variant=40971840487599&stkn=85ef6db07253&gad_campaignid=20344892290) instead of [Official motion sensor](https://www.switchbot.jp/products/switchbot-motion-sensor).

## 🌍 Environment

### Hardware Requirements

#### Components

| Component | Model/Specification |
|---------------|----------|
| [ESP32](https://akizukidenshi.com/catalog/g/g115674/) | ESP32-DevKitC-VE |
| [PIR sensor](https://akizukidenshi.com/catalog/g/g114064/) | SB612B |
| [Tactile switch](https://akizukidenshi.com/catalog/g/g109826/) | Any tactile switch |
| [Breadboard](https://akizukidenshi.com/catalog/g/g100315/) | Any standard breadboard |
| [Battery box](https://akizukidenshi.com/catalog/g/g111523/) | SBH-321-3AS150 |
| [Lighting Device](https://www.switchbot.jp/products/switchbot-color-bulb) | SwitchBot Color Bulb |

#### Connection Configuration

```txt
ESP32:
├── SB612B (PIR)
│   ├── GPIO 26 -----> IN
│   ├── GND ---------> GND
│   └── 3.3V --------> VCC
├── Tactile switch
│   ├── GPIO 27 -----> IN
│   ├── GND ---------> GND
└── USB  → PC or Power Supply
```

<img src=/resources/images/original_motion_sensor.jpg width= "600px" >

## 🚀 Setup

### 1. Initial setup

- In advance, you must complete the setup according to [Setup](/README.md#-setup).

### 2. Register SwitchBot product

- If you register original device names in `device_config.py`, update `original_motion_sensor/factory.py`

```python
target_mac = DEVICE_CONFIG["color_bulb"]["<your_device_name>"]["ble_mac_address"]
```

### 3. Upload

- To upload the program, run `MicroPico: Upload project to Pico`
- Add the following settings in `setting.json` to prevent unnecessary files from being uploaded to the device:

```json
{
    "micropico.pyIgnore": [
        "**/.picowgo",
        "**/.micropico",
        "**/.vscode",
        "**/.gitignore",
        "**/.git",
        "**/.DS_Store",
        "**/project.pico-go",
        "**/env",
        "**/venv",
        "**/.venv",
        "**/.idea",
        "**/node_modules",
        "**/resources",
        "**/docs",
        "**/package.json",
        "**/package-lock.json"
    ]
}
```

### 4. Launch

- To run the program, run `MicroPico: Run current file on Pico` in the `main.py`

## 🎮 Usage

### Basic Operation

1. Boot phase
    - After the ESP32 boots up, it automatically establishes a BLE connection with the SwitchBot color bulb.
1. Motion detection
    - When the PIR sensor detects motion, the bulb is automatically turned on.
1. Automatic turn-off
    - The bulb is automatically turned off after a specified time.
1. Sleep mode
    - If the motion sensor don't detect for a specified time, the system enter the light or deep sleep.
    - Resume with GPIO interrupt.
1. Manual reboot
    - Pressing the button reboots the system.

### Customization

- Configure the operation time in `original_motion_sensor/config/constants.py`

  ```python
  POWER_ON_DURATION = 1 * minutes
  LIGHT_SLEEP_DURATION = 30 * seconds
  LIGHT_SLEEP_THRESHOLD = 30 * minutes
  DEEP_SLEEP_THRESHOLD = 1 * hours
  ```

## 💡 Motivation for it

I bought [SwitchBot Color Bulb](https://www.switchbot.jp/products/switchbot-color-bulb) to automate a home lighting system with [Official motion sensor](https://www.switchbot.jp/products/switchbot-motion-sensor).  
Basically, it works well, but a detectable distance of the motion sensor is very short against the nominal value.  
Actually, it can detect an object within 3 meters (the nominal value is within 7 meters).  
It is not enough distance even in my apartment's corridor.  
Thats' why, I started developing the original motion sensor instead of the official product.  
By implementing sleep mode, I realized sufficient detection distance while also considering battery-powered operation.  
