# SwitchMate

Original IoT projects that collaborate with SwitchBot products.  
This repository is expected to have multiple projects.  
Each project has specific requirements in addition to the following, so please refer to the README for each project.

## 🌍 Environment

### Software Requirements

- OS
  - Windows 10/11
- Language
  - MicroPython v1.26.1
- IDE
  - VSCode (Recommended)
  - [MicroPico](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go)

## 🚀 Setup

### 1. Install MicroPython

- Write MicroPython firmware to ESP32.

```bash
# Download firmware
# https://micropython.org/download/ESP32_GENERIC/

# Install esptool
$ pip install esptool

# Erase and write firmware
$ esptool --port <your_port> erase_flash
$ esptool --chip esp32 --port <your_port> --baud 460800 write_flash -z 0x1000 <firmware_file>.bin
```

### 2. Clone Repository

```bash
$ git clone https://github.com/na-yusuke/SwitchMate.git
or
$ git clone git@github.com:na-yusuke/SwitchMate.git
```

### 3. Install MicroPico Extension (if using VSCode)

- Follow this instructions: [Getting started](https://github.com/paulober/MicroPico?tab=readme-ov-file#getting-started)
- Add the following settings in `setting.json` to prevent unnecessary files from being uploaded to the device:

```json
{
    "micropico.pyIgnore": [
        "**/.claude",
        "**/.DS_Store",
        "**/.git",
        "**/.gitignore",
        "**/.idea",
        "**/.micropico",
        "**/.picowgo",
        "**/.venv",
        "**/.vscode",
        "**/docs",
        "**/env",
        "**/node_modules",
        "**/package-lock.json",
        "**/package.json",
        "**/project.pico-go",
        "**/resources",
        "**/venv"
    ]
}
```

### 4. Configuration

#### `config.py`

```bash
$ cp config.example.py config.py
```

- Edit `config.py` for SwitchBot BLE API
  - Follow the [SwitchBotAPI-BLE](https://github.com/OpenWonderLabs/SwitchBotAPI-BLE), specify the UUIDs depending on your device type.
  - You can confirm the Web API token and secret on SwitchBot app.

```python
# SwitchBot BLE API
SWITCHBOT_SERVICE_UUID = "SWITCHBOT_SERVICE_UUID"
SWITCHBOT_CHARACTERISTIC_UUID = "SWITCHBOT_CHARACTERISTIC_UUID"

# SwitchBot Web API
SWITCHBOT_BASE_URL = "SWITCHBOT_BASE_URL"
SWITCHBOT_API_TOKEN = "YOUR_SWITCHBOT_API_TOKEN"
SWITCHBOT_API_CLIENT_SECRET = "YOUR_SWITCHBOT_API_CLIENT_SECRET"
```

#### `device_config.py`

```bash
$ cp device_config.example.py device_config.py
```

- Edit `device_config.py` according to the SwitchBot products you manage.
  - You can confirm `ble_mac_address` on SwitchBot app.

```python
DEVICE_CONFIG = {
    "color_bulb": {
        "<your_device_name>": {
            "name": "<your_device_name>",
            "ble_mac_address": "XX:XX:XX:XX:XX:XX",
        },
    }
}
```

### 4. Each project setting

- Once complete the setup, proceed to the setup for each project.

## 🔮 Projects

- [Original motion Sensor](/original_motion_sensor//README.md)

## 📚 References

- [MicroPython ライブラリ bluetooth --- 低レベル Bluetooth](https://micropython-docs-ja.readthedocs.io/ja/latest/library/bluetooth.html)
- [MicroPython libraries time – time related functions](https://docs.micropython.org/en/latest/library/time.html)
- [MicroPython ライブラリ esp32 --- EDS32 に固有の機能](https://micropython-docs-ja.readthedocs.io/ja/latest/library/esp32.html)
- [IoT を使ってみる（その１５：ESP32のディープスリープで長時間バッテリー駆動に挑戦）](https://developer.mamezou-tech.com/iot/internet-of-things-15/)
- [IoT を使ってみる（その２０：MicroPythonで始めるESP32プログラミング「超」入門）](https://developer.mamezou-tech.com/iot/internet-of-things-20/)
- [SwitchBot BLE API](https://github.com/OpenWonderLabs/SwitchBotAPI-BLE)
- [SwitchBot API v1.1](https://github.com/OpenWonderLabs/SwitchBotAPI)
- [MicroPico](https://github.com/paulober/MicroPico)
