from shared import get_logger

from .base import BaseApi

logger = get_logger("SceneApi")


class SceneApi(BaseApi):
    """SwitchBot Scene API"""

    def get_scenes(self):
        """Get scene list"""
        return self.__make_request("GET", "/scenes")

    def execute_scene(self, scene_id):
        """Execute scene"""
        return self.__make_request("POST", f"/scenes/{scene_id}/execute")

    def print_scenes(self):
        """Print scene list in readable format"""
        scenes_data = self.get_scenes()

        if not scenes_data:
            logger.warning("Failed to get scenes")
            return

        if "body" not in scenes_data:
            logger.warning("No scene data found")
            return

        body = scenes_data["body"]
        logger.info("=== SwitchBot Scenes ===")

        if isinstance(body, list):
            for scene in body:
                logger.info(f"- {scene.get('sceneName', 'Unknown')}")
                logger.info(f"  ID: {scene.get('sceneId', 'Unknown')}")
                logger.info()
        else:
            logger.warning("No scenes found")

        logger.info("========================")
