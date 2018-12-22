# coding=utf-8
import scrapy
from scrapy.selector import Selector, SelectorList
from scrapy.http import FormRequest
from scrapper.util.extractor import Extractor
from scrapper.util.structure import Structure

class EenTweeDrieWonenSpider(scrapy.Spider):
    name = '123WonenSpider'
    allowed_domains = ["www.123wonen.nl"]

    def __init__(self, queryRegion='Amersfoort'):
        self.region = queryRegion.title()

    def start_requests(self):
        # 123wonen.nl url's do not determine the content. The query results are fetched
        # from the session storage which we can influence by POSTing a new query
        return [
            FormRequest(
                "https://www.123wonen.nl/huurwoningen",
                formdata={
                    'cm01': '1',
                    'redirecturl': 'huurwoningen',
                    'pricerange': '-',
                    'city': self.region,
                    'zipcoder': '0',
                    'price_start': '0',
                    'price_end': '0'
                },
                callback=self.parse
            )
        ]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.pandlist-container')
        objects.extract()

        for index, object in enumerate(objects):
            # Determine if the object is still available for rent
            objectStatus = str(Extractor.string(object, '.pand-status')).lower()
            if objectStatus in ['verhuurd', 'in optie']:
                continue

            # Skip crawling storage spaces and garages
            type = Structure.find_in_definition(object, '.pand-specs li > span', 'Type').lower()
            if type in ['garagebox', 'berging/opslag', 'kantoorruimte', 'loods', 'parkeerplaats', 'winkelpand']:
                continue

            yield scrapy.Request(
                Extractor.string(object, 'a.textlink-design:contains("Details")::attr(href)'),
                self.parse_object
            )

        # Crawl the next pages
        nextPageSelector = '.productBrowser a:contains("volgende")'
        nextPageLink = pageSelector.css(nextPageSelector).extract_first()
        if nextPageLink is not None and isinstance(nextPageLink, str):
            nextPageSelector += '::attr(href)'
            yield scrapy.Request(
                Extractor.url(response, pageSelector, nextPageSelector),
                self.parse,
            )

    def parse_object(self, response):
        breadCrumbTitle = Extractor.string(response, 'a.active span').split(' - ')
        city = Extractor.string(breadCrumbTitle[0])
        breadCrumbTitle.pop(0)
        street = ' - '.join(breadCrumbTitle)

        volume = Structure.find_in_definition(response, '.pand-specs.panddetail-desc li > span', 'Woonoppervlakte')
        if volume is not None and isinstance(volume, str):
            volume = Extractor.volume(volume)

        rooms = Structure.find_in_definition(response, '.pand-specs.panddetail-desc li > span', 'Kamers')
        if rooms is not None and isinstance(rooms, str):
            Extractor.string(rooms)

        type = Structure.find_in_definition(response, '.pand-specs.panddetail-desc li > span', 'Type')
        if type is not None and isinstance(type, str):
            Extractor.string(type)

        price = Extractor.string(response, '.panddetail-price')
        price = price.split('-')[0]
        price = Extractor.euro(price)

        availability = Structure.find_in_definition(response, '.pand-specs.panddetail-desc li > span', 'Beschikbaarheid')
        if availability is not None and isinstance(type, str):
            availability = Extractor.string(availability)

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
            'estateAgent': '123Wonen.nl',
            'images': Extractor.images(response, 'a[data-fancybox="group1"]::attr(href)', True),
        }
