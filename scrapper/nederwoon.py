# coding=utf-8
import scrapy
from urlparse import urlparse
from scrapy.selector import Selector
from util.extractor import Extractor

class NederwoonSpider(scrapy.Spider):
    name = 'nederwoonspider'
    allowed_domains = ["www.nederwoon.nl"]

    def __init__(self, queryCity='amersfoort'):
        self.start_urls = [('http://www.nederwoon.nl/huurwoningen/{0}?numberviews=1000&rows=1000&q='.format(queryCity))]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('form#searchform div#cont_element75')
        objects.extract()

        for index, object in enumerate(objects):
            # Determine if the object is the right type
            type = str(Extractor.string(object, 'div[data-object-kenmerk="type"]')).lower()
            if type != 'appartement' and type != 'kamer' and type != "studio":
                continue

            # Parse Path and send another request
            path = object.css('a.green.underlined').re_first(r'href="\s*(.*)\" class')
            parsed_uri = urlparse(response.url)
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

            # Nederwoon does not correctly show the availability date in the detail page, pass the date as meta
            meta = {'Type': type, 'Availability': Extractor.string(object, '[data-object-kenmerk="beschikbaarheid"]')}
            yield scrapy.Request(domain + path, self.parse_object, 'GET', None, None, None, meta)

    def parse_object(self, response):
        cityStreet = Extractor.string(response, '[data-object-kenmerk="straatnaam"]').split(', ')
        volume = Extractor.string(response, '[data-object-kenmerk="woonoppervlakte"]').replace('m2', '')
        rooms = Extractor.string(response, '[data-object-kenmerk="slaapkamers"]')
        price = Extractor.eurosAsFloat(response, '.price_red')

        yield {
            'street': cityStreet[0],
            'city': cityStreet[1],
            'volume': volume,
            'rooms': rooms,
            'availability': response.meta['Availability'],
            'type': response.meta['Type'],
            'price': price,
            'reference': response.url
        }
