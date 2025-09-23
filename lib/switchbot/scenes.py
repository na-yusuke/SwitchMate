from .base import BaseAPI


class SceneAPI(BaseAPI):
    """SwitchBot シーン関連API"""

    def get_scenes(self):
        """シーン一覧を取得"""
        return self.__make_request('GET', '/scenes')

    def execute_scene(self, scene_id):
        """シーンを実行"""
        return self.__make_request('POST', f'/scenes/{scene_id}/execute')

    def print_scenes(self):
        """シーン一覧を見やすく表示"""
        scenes_data = self.get_scenes()

        if not scenes_data:
            print("Failed to get scenes")
            return

        if 'body' not in scenes_data:
            print("No scene data found")
            return

        body = scenes_data['body']
        print("=== SwitchBot Scenes ===")

        if isinstance(body, list):
            for scene in body:
                print(f"- {scene.get('sceneName', 'Unknown')}")
                print(f"  ID: {scene.get('sceneId', 'Unknown')}")
                print()
        else:
            print("No scenes found")

        print("========================")