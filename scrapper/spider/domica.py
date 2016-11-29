# coding=utf-8
import scrapy
from urlparse import urlparse
from scrapy.selector import Selector
from scrapper.util.extractor import Extractor
from scrapper.util.structure import Structure


class DomicaSpider(scrapy.Spider):
    name = 'domicaspider'
    allowed_domains = ["www.domica.nl"]

    def __init__(self, queryCity='Amersfoort', queryCityId='69'):
        self.start_urls = [
            (
                'http://www.domica.nl/12-cff6/aanbod-resultaten?' +
                'PropertyType=Residential&ForSaleOrRent=FOR_RENT&Take=1000&TypeGroups[0]=19&' +
                'LocationOfInterest={0}&AdminAreaLevel2ID={1}'
                .format(queryCity, queryCityId)
            )
        ]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.object_list_container .row.object')
        objects.extract()

        for index, object in enumerate(objects):
            # Determine if the object is still available for rent
            objectStatus = str(Extractor.string(object, '.object_status')).lower()
            if objectStatus == '' or objectStatus == 'verhuurd':
                continue

            # Parse Path and send another request
            path = object.css('div.datacontainer > a').re_first(r'href="\s*(.*)\"')
            parsed_uri = urlparse(response.url)
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

            yield scrapy.Request(domain + path, self.parse_object)

    def parse_object(self, response):
        adress = Extractor.string(response, '.address').split(' ')
        street = adress[0][0:-1]
        city = adress[(len(adress) - 1)]

        volume = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Perceeloppervlakte')
        if volume is not None and isinstance(volume, basestring):
            volume = Extractor.volume(volume)

        rooms = Structure.find_in_definition(response, 'table.table-striped.feautures tr td', 'Aantal kamers')
        if rooms is not None and isinstance(rooms, basestring):
            rooms = rooms.split(' (w')[0]

        availability = Structure.find_in_definition(
            response,
            'table.table-striped.feautures tr td',
            'Beschikbaar vanaf'
        )

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
            'availability': availability,
            'type': type,
            'price': price,
            'reference': response.url
        }
