from switchbot_api import SwitchBotAPI
from switchbot_api import SwitchBotAPI

def main():
    print("Starting SwitchBot device list retrieval...")
    switchbot = SwitchBotAPI()
    switchbot.print_devices()

if __name__ == "__main__":
    main()
