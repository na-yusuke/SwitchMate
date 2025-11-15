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

        if isinstance(body, list):
            scenes_list = []
            for scene in body:
                scene_name = scene.get("sceneName", "Unknown")
                scene_id = scene.get("sceneId", "Unknown")
                scenes_list.append(f"{scene_name} (ID: {scene_id})")

            logger.debug(f"SwitchBot Scenes: {', '.join(scenes_list)}")
        else:
            logger.warning("No scenes found")
