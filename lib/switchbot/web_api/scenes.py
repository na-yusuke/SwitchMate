from .base import BaseApi


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
            print("Failed to get scenes")
            return

        if "body" not in scenes_data:
            print("No scene data found")
            return

        body = scenes_data["body"]
        print("=== SwitchBot Scenes ===")

        if isinstance(body, list):
            for scene in body:
                print(f"- {scene.get('sceneName', 'Unknown')}")
                print(f"  ID: {scene.get('sceneId', 'Unknown')}")
                print()
        else:
            print("No scenes found")

        print("========================")
