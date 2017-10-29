# coding=utf-8
import scrapy
import re
from scrapy.selector import Selector

from scrapper.util.extractor import Extractor
from scrapper.util.structure import Structure


class NederwoonSpider(scrapy.Spider):
    name = 'nederwoonspider'
    allowed_domains = ["www.nederwoon.nl"]

    def __init__(self, queryRegion='amersfoort'):
        self.region = queryRegion.title()
        self.start_urls = ['http://www.nederwoon.nl/huurwoningen/{0}'.format(queryRegion)]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.location')
        objects.extract()

        for index, object in enumerate(objects):
            objectUrl = Extractor.url(response, object, 'h2.heading-sm > a::attr(href)')
            yield scrapy.Request(objectUrl, self.parse_object)

    def parse_object(self, response):
        street = Extractor.string(response, 'h1.text-regular')
        city = Extractor.string(response, '.col-md-8 .fixed-lh p.color-medium')
        availability = Extractor.string(response, '.col-md-8 .horizontal-items ul li:last-child')

        # Sometimes Nederwoon mistakenly adds the zip code in the city field, filter it out
        city = re.sub('\d{4}?\s*[a-zA-Z]{2}', '', city).replace(' ', '')

        rooms = Extractor.string(
            Structure.find_in_definition(response, '.table-striped.table-specs td', 'Aantal kamers')
        )
        price = Extractor.euro(
            Structure.find_in_definition(response, '.table-striped.table-specs td', 'Totale huur per maand', 2)
        )
        volume = Extractor.volume(
            Structure.find_in_definition(response, '.table-striped.table-specs td', 'Woonoppervlakte')
        )
        type = Extractor.string(
            Structure.find_in_definition(response, '.table-striped.table-specs td', 'Soort woonruimte')
        )

        yield {
            'street': street,
            'city': city,
            'region': self.region,
            'volume': volume,
            'rooms': rooms,
            'availability': availability,
            'type': type,
            'pricePerMonth': price,
            'reference': Extractor.urlWithoutQueryString(response),
            'estateAgent': 'NederWoon'
        }
