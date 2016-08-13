import scrapy
from urlparse import urlparse
from scrapy.selector import Selector

class NederwoonSpider(scrapy.Spider):
    name = 'nederwoonspider'
    start_urls = ['http://www.nederwoon.nl/huurwoningen/amersfoort?numberviews=1000&rows=1000&q=']

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.xpath('//*[@id="cont_element75"]')

        for index, object in enumerate(objects):
            # Determine if object is worth further investigating
            priceText = object.xpath('//*[@class="price_red"]/text()').extract()[index].strip().replace('.','').replace(',', '.')
            priceValue = float(priceText[2:])

            if priceValue > 350.0 and priceValue < 900.0:
                # Parse Path and send another request
                path = object.xpath('//*[@class="btn_green"]/@onclick').extract()[index]
                path = path.replace(' ', '').replace('document.location.href=\'', '').replace('?sighting=true\'', '')
                parsed_uri = urlparse(response.url)
                domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
                yield scrapy.Request(domain + path, self.parse_object)

    def parse_object(self, response):
            yield {'url': response.url}
