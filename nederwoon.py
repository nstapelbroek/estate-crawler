# coding=utf-8
import os
import scrapy
from urlparse import urlparse
from scrapy.selector import Selector
from configobj import ConfigObj
from scrapper.util.extractor import Extractor

class NederwoonSpider(scrapy.Spider):
    name = 'nederwoonspider'
    config = ConfigObj(os.getcwd() + '/config.ini')
    start_urls = [('http://www.nederwoon.nl/huurwoningen/{0}?numberviews=1000&rows=1000&q='.format(config['place']))]

    def getConfig(self):
        return ConfigObj(os.getcwd() + '/config.ini')

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('form#searchform div#cont_element75')
        objects.extract()

        for index, object in enumerate(objects):
            #Determine if the object is the right type
            type = str(Extractor.string(object, 'div[data-object-kenmerk="type"]')).lower()
            if type != 'appartement' and type != 'kamer' and type != "studio":
                continue

            # Parse Path and send another request
            # path = object.css('.btn_green').re_first(r'href=\'\s*(.*)\?sighting=true')
            path = object.css('a.green.underlined').re_first(r'href="\s*(.*)\" class')
            parsed_uri = urlparse(response.url)
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            yield scrapy.Request(domain + path, self.parse_object)

    def parse_object(self, response):
        street = Extractor.string(response, '[data-object-kenmerk="straatnaam"]')
        volume = Extractor.string(response, '[data-object-kenmerk="woonoppervlakte"]').replace('m2', '')
        rooms = Extractor.string(response, '[data-object-kenmerk="slaapkamers"]')
        availability = Extractor.string(response, '[data-object-kenmerk="beschikbaarheid"]')
        price = Extractor.eurosAsFloat(response, '.price_red')

        yield {
            'street': street,
            'volume': volume,
            'rooms': rooms,
            'availability': availability,
            'price': price,
            'reference': response.url
        }
