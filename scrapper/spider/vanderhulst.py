# coding=utf-8
import scrapy
from scrapy.selector import Selector

from scrapper.util.extractor import Extractor
from scrapper.util.structure import Structure


class VanderHulstSpider(scrapy.Spider):
    name = 'van der Hulst'
    allowed_domains = ["vanderhulstverhuurmakelaar.nl"]

    def __init__(self, queryRegion='amersfoort'):
        self.region = queryRegion.title()
        self.start_urls = ['https://vanderhulstverhuurmakelaar.nl/location/{0}/'.format(queryRegion)]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('article.property')
        objects.extract()

        for index, object in enumerate(objects):
            # Determine if the object is still available for rent
            objectStatus = str(Extractor.string(object, '.property-row-meta-item-status > strong')).lower()
            if objectStatus in ['verhuurd', 'in optie', 'onder opti e']:
                continue

            objectUrl = Extractor.string(object, 'a.property-row-image::attr(href)')
            yield scrapy.Request(objectUrl, self.parse_object)

    def parse_object(self, response):
        tableSelector = '.property-overview dl > *'

        yield {
            'street': Extractor.string(response, 'h1.entry-title'),
            'city': Extractor.string(Structure.find_in_definition(response, tableSelector, 'Plaats')).title(),
            'region': self.region,
            'volume': Extractor.volume(Structure.find_in_definition(response, tableSelector, 'Woonoppervlakte')),
            'rooms': Extractor.string(Structure.find_in_definition(response, tableSelector, 'Kamers')),
            'availability': Extractor.string(Structure.find_in_definition(response, tableSelector, 'Status')),
            'type': Extractor.string(Structure.find_in_definition(response, tableSelector, 'Type')),
            'pricePerMonth': Extractor.euro(Structure.find_in_definition(response, tableSelector, 'Prijs')),
            'reference': Extractor.urlWithoutQueryString(response),
            'estateAgent': 'Van der Hulst',
            'images': Extractor.images(response, '.property-detail-gallery a::attr(href)', True),
        }
