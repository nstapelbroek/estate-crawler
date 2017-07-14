import requests

class Api(object):

    def process_item(self, item, spider):
        settings = spider.settings
        apiUrl = (settings.get('SCRAPPER_API_URL'))

        if isinstance(apiUrl, str):
            requests.post(apiUrl, item)

        return item