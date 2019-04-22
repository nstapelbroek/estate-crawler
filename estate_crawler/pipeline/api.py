import requests


class Api(object):
    def process_item(self, item, spider):
        settings = spider.settings
        apiUrl = settings.get("SCRAPPER_API_URL")

        if isinstance(apiUrl, str):
            headers = {"content-type": "application/json"}
            requests.post(apiUrl, json=item, headers=headers)

        return item
