from utils import get_logger

from .base import BaseApi

logger = get_logger("DeviceApi")


class DeviceApi(BaseApi):
    """SwitchBot Device API"""

    def get_devices(self):
        """Get device list"""
        return self.__make_request("GET", "/devices")

    def get_device_status(self, device_id):
        """Get device status"""
        return self.__make_request("GET", f"/devices/{device_id}/status")

    def control_device(self, device_id, command, parameter=None):
        """Control device"""
        data = {"command": command, "parameter": parameter or "default"}
        return self.__make_request("POST", f"/devices/{device_id}/commands", data)

    def print_devices(self):
        """Print device list in readable format"""
        devices_data = self.get_devices()

        if not devices_data:
            logger.warning("Failed to get devices")
            return

        if "body" not in devices_data:
            logger.warning("No device data found")
            return

        body = devices_data["body"]
        logger.info("=== SwitchBot Devices ===")

        if "deviceList" in body and body["deviceList"]:
            logger.info("\n[Physical Devices]")
            for device in body["deviceList"]:
                logger.info(f"- {device.get('deviceName', 'Unknown')} ({device.get('deviceType', 'Unknown')})")
                logger.info(f"  ID: {device.get('deviceId', 'Unknown')}")
                if "hubDeviceId" in device:
                    logger.info(f"  Hub: {device['hubDeviceId']}")
                logger.info()

        if "infraredRemoteList" in body and body["infraredRemoteList"]:
            logger.info("[Virtual Infrared Devices]")
            for device in body["infraredRemoteList"]:
                logger.info(f"- {device.get('deviceName', 'Unknown')} ({device.get('remoteType', 'Unknown')})")
                logger.info(f"  ID: {device.get('deviceId', 'Unknown')}")
                if "hubDeviceId" in device:
                    logger.info(f"  Hub: {device['hubDeviceId']}")
                logger.info()

        logger.info("========================")

    def turn_on_device(self, device_id):
        """Turn on SwitchBot device"""
        return self.control_device(device_id, "turnOn")

    def turn_off_device(self, device_id):
        """Turn off SwitchBot device"""
        return self.control_device(device_id, "turnOff")
