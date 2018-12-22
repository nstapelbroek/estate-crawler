# coding=utf-8
import scrapy
from scrapy.selector import Selector
from scrapper.util.extractor import Extractor
from scrapper.util.structure import Structure


class DomicaSpider(scrapy.Spider):
    name = 'domicaspider'
    allowed_domains = ["www.domica.nl"]

    def __init__(self, queryRegion='Amersfoort'):
        self.region = queryRegion.title()
        self.start_urls = [
            (
                'https://www.domica.nl/woningaanbod/huur/land-nederland/gemeente-{0}/type-appartement'
                .format(queryRegion)
            )
        ]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.object_list_container .row.object')
        objects.extract()

        for index, object in enumerate(objects):
            # Determine if the object is still available for rent
            objectStatus = str(Extractor.string(object, '.object_status')).lower()
            if objectStatus == 'verhuurd':
                continue

            # Pass the availability from the overview, since it's listed in DD-MM-YYYY format on the overview page
            objectAvailibility = str(Extractor.string(object, '.object_availability > span'))
            meta = {'availability': objectAvailibility}

            # Parse Path and send another request
            object_url = Extractor.url(response, object, 'div.datacontainer > a::attr(href)')

            yield scrapy.Request(object_url, self.parse_object, 'GET', None, None, None, meta)

    def parse_object(self, response):
        address_heading = Extractor.string(response, '.address').split(',')
        street = address_heading[0]
        postcode_and_city = address_heading[1].split(' ')
        city = postcode_and_city[(len(postcode_and_city) - 1)]

        volume = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Gebruiksoppervlakte wonen')
        if volume is not None and isinstance(volume, str):
            volume = Extractor.volume(volume)

        rooms = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Aantal kamers')
        if rooms is not None and isinstance(rooms, str):
            rooms = rooms.split(' (w')[0]

        type = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Type object')
        if type is not None and isinstance(type, str):
            type = type.split(', ')
            lastindex = (len(type) - 1)
            type = type[lastindex]

        price = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Prijs')
        if price is not None and isinstance(type, str):
            price = Extractor.euro(price.split('-')[0])

        yield {
            'street': street,
            'city': city,
            'region': self.region,
            'volume': volume,
            'rooms': rooms,
            'availability': response.meta['availability'],
            'type': type,
            'pricePerMonth': price,
            'reference': Extractor.urlWithoutQueryString(response),
            'estateAgent': 'Domica',
            'images': Extractor.images(response, '#cycle-slideshow2 > a.gallery-link img::attr(src)', True),
        }
