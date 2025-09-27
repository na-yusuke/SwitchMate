from .base import BaseApi


class WebhookApi(BaseApi):
    """SwitchBot Webhook関連API"""

    def get_webhook_config(self):
        """Webhook設定を取得"""
        return self.__make_request('GET', '/webhook/queryUrl')

    def setup_webhook(self, url):
        """Webhookを設定"""
        data = {
            'action': 'setupWebhook',
            'url': url
        }
        return self.__make_request('POST', '/webhook/setupWebhook', data)

    def delete_webhook(self, url):
        """Webhookを削除"""
        data = {
            'action': 'deleteWebhook',
            'url': url
        }
        return self.__make_request('POST', '/webhook/deleteWebhook', data)

    def query_webhook_details(self, urls):
        """Webhook詳細を取得"""
        data = {
            'action': 'queryDetails',
            'urls': urls if isinstance(urls, list) else [urls]
        }
        return self.__make_request('POST', '/webhook/queryDetails', data)