import scrapy
from scrapy.selector import Selector

from scrapper.util.extractor import Extractor
from scrapper.util.structure import Structure


class RotsvastSpider(scrapy.Spider):
    name = 'RotsvastSpider'
    allowed_domains = ["www.rotsvast.nl"]

    def __init__(self, queryRegion='amersfoort'):
        self.region = queryRegion.title()
        self.start_urls = ['https://www.rotsvast.nl/woningaanbod/?type=2&city={0}&type1[]=Appartement&type1[]=Woonhuis&display=list&count=60'.format(queryRegion)]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.residence-list.clickable-parent')
        objects.extract()

        for index, object in enumerate(objects):
            objectUrl = Extractor.string(object, 'a.clickable-block::attr(href)')

            # Extracting the street is a lot easier in the overview page, so we'll pass it into the meta
            street = Extractor.string(object, '.residence-street')
            city = Extractor.string(object, '.residence-zipcode-place').split(" ")[1:]
            city = " ".join(city)
            meta = {'street': street, 'city': city}

            yield scrapy.Request(objectUrl, self.parse_object, 'GET', None, None, None, meta)

    def parse_object(self, response):
        availability = Extractor.string(
            Structure.find_in_definition(response, '#properties .row > .col-xs-6', 'Ingangsdatum')
        )
        rooms = Extractor.string(
            Structure.find_in_definition(response, '#properties .row > .col-xs-6', 'Aantal kamers')
        )
        price = Extractor.euro(
            Structure.find_in_definition(response, '#properties .row > .col-xs-6', 'Totale huur').split('-')[0]
        )
        volume = Extractor.volume(
            Structure.find_in_definition(response, '#properties .row > .col-xs-6', 'Oppervlakte (ca.)')
        )
        type = Extractor.string(
            Structure.find_in_definition(response, '#properties .row > .col-xs-6', 'Soort')
        )

        yield {
            'street': response.meta['street'],
            'city': response.meta['city'],
            'region': self.region,
            'volume': volume,
            'rooms': rooms,
            'availability': availability,
            'type': type,
            'pricePerMonth': price,
            'reference': Extractor.urlWithoutQueryString(response),
            'estateAgent': 'Rotsvast',
            'images': Extractor.images(response, '.slider img::attr(src)', True),
        }
