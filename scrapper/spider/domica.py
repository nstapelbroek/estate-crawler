# coding=utf-8
import scrapy
from urlparse import urlparse
from scrapy.selector import Selector
from scrapper.util.extractor import Extractor
from scrapper.util.structure import Structure


class DomicaSpider(scrapy.Spider):
    name = 'domicaspider'
    allowed_domains = ["www.domica.nl"]

    def __init__(self, queryCity='Amersfoort'):
        self.start_urls = [
            (
                'https://www.domica.nl/woningaanbod/huur/land-nederland/gemeente-{0}/type-appartement'
                .format(queryCity)
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
            path = object.css('div.datacontainer > a').re_first(r'href="\s*(.*)\"')
            parsed_uri = urlparse(response.url)
            domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

            yield scrapy.Request(domain + path, self.parse_object, 'GET', None, None, None, meta)

    def parse_object(self, response):
        address_heading = Extractor.string(response, '.address').split(',')
        street = address_heading[0]
        postcode_and_city = address_heading[1].split(' ')
        city = postcode_and_city[(len(postcode_and_city) - 1)]

        volume = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Gebruiksoppervlakte wonen')
        if volume is not None and isinstance(volume, basestring):
            volume = Extractor.volume(volume)

        rooms = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Aantal kamers')
        if rooms is not None and isinstance(rooms, basestring):
            rooms = rooms.split(' (w')[0]

        type = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Type object')
        if type is not None and isinstance(type, basestring):
            type = type.split(', ')
            lastindex = (len(type) - 1)
            type = type[lastindex]

        price = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Prijs')
        if price is not None and isinstance(type, basestring):
            price = Extractor.euro(price.split('-')[0])

        yield {
            'street': street,
            'city': city,
            'volume': volume,
            'rooms': rooms,
            'availability': response.meta['availability'],
            'type': type,
            'pricePerMonth': price,
            'reference': response.url,
            'estateAgent': 'Domica'
        }
