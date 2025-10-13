from .base import BaseApi


class WebhookApi(BaseApi):
    """SwitchBot Webhook API"""

    def get_webhook_config(self):
        """Get webhook configuration"""
        return self.__make_request("GET", "/webhook/queryUrl")

    def setup_webhook(self, url):
        """Setup webhook"""
        data = {"action": "setupWebhook", "url": url}
        return self.__make_request("POST", "/webhook/setupWebhook", data)

    def delete_webhook(self, url):
        """Delete webhook"""
        data = {"action": "deleteWebhook", "url": url}
        return self.__make_request("POST", "/webhook/deleteWebhook", data)

    def query_webhook_details(self, urls):
        """Get webhook details"""
        data = {
            "action": "queryDetails",
            "urls": urls if isinstance(urls, list) else [urls],
        }
        return self.__make_request("POST", "/webhook/queryDetails", data)
