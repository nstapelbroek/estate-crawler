# coding=utf-8
import os
import scrapy
from urlparse import urlparse
from scrapy.selector import Selector
from configobj import ConfigObj
from htmllaundry import strip_markup


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
            type = str(self.extractString(object, 'div[data-object-kenmerk="type"]'))
            if type != 'appartement' and type != 'kamer':
                continue

            # Parse Path and send another request
            path = object.css('.btn_green').re_first(r'href=\'\s*(.*)\?sighting=true')
            parsed_uri = urlparse(response.url)
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            yield scrapy.Request(domain + path, self.parse_object)

    def parse_object(self, response):
        street = self.extractString(response, '[data-object-kenmerk="straatnaam"]')
        volume = self.extractString(response, '[data-object-kenmerk="woonoppervlakte"]').replace('m2', '')
        rooms = self.extractString(response, '[data-object-kenmerk="slaapkamers"]')
        availability = self.extractString(response, '[data-object-kenmerk="beschikbaarheid"]')
        price = self.extractEurosAsFloat(response, '.price_red')

        yield {
            'street': street,
            'volume': volume,
            'rooms': rooms,
            'availability': availability,
            'price': price,
            'reference': response.url
        }

    def extractEurosAsFloat(self, html, cssSelector):
        data = self.extractString(html, cssSelector)
        data = data.replace('.', '').replace(',', '.').replace('€', '')
        return float(data)

    def extractString(self, html, cssSelector):
        if not isinstance(html, Selector):
            html = Selector(html)

        data = html.css(cssSelector).extract_first()
        data = str(strip_markup(data).encode('utf-8'))
        return data.strip()

