# coding=utf-8
import re
import scrapy

from scrapy.exceptions import NotSupported
from scrapy.selector import Selector
from scrapy.http import FormRequest
from estate_crawler.util import Extractor, Structure


class Domica(scrapy.Spider):
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
        objects.getall()

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

        volume = Structure.find_in_definition(response, 'table.table-striped.feautures tr td',
                                              'Gebruiksoppervlakte wonen')
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
            'images': Extractor.images(response, '#cycle-slideshow2 > a.gallery-link img::attr(estate_crawler)', True),
        }


class EenTweeDrieWonen(scrapy.Spider):
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
        objects.getall()

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
        nextPageLink = pageSelector.css(nextPageSelector).get()
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

        availability = Structure.find_in_definition(response, '.pand-specs.panddetail-desc li > span',
                                                    'Beschikbaarheid')
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


class Eervast(scrapy.Spider):
    name = 'eervastspider'
    allowed_domains = ["www.eervast.nl"]

    def __init__(self, queryRegion='amersfoort'):
        self.region = queryRegion.title()
        if queryRegion.lower() != 'amersfoort':
            raise NotSupported

    def build_request(self, type):
        return FormRequest(
            "http://www.eervast.nl/includes/php/huren-search.php",
            formdata={
                'type': type,
                'beschikbaarheid': '0',
                'inrichting': '0',
                'ordering': '3',
                'prijs_van': '0',
                'prijs_tot': '5000'
            },
            callback=self.parse
        )

    def start_requests(self):
        types = ['4', '10', '20']  # Initially only look for apartments and studios
        requests = []
        for type in types:
            requests.append(self.build_request(type))
        return requests

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.home-house')
        objects.getall()

        for index, object in enumerate(objects):
            object_url = Extractor.url(response, object, '.house-button a::attr(href)')

            # Extracting the street is a lot easier in the overview page, so we'll pass it into the meta
            street = Extractor.string(object, '.home-house-info h2')
            city = Extractor.string(object, '.home-house-info h3').split(" ")
            city = city[len(city) - 1]
            meta = {'street': street, 'city': city}
            yield scrapy.Request(object_url, self.parse_object, 'GET', None, None, None, meta)

    def parse_object(self, response):
        type = Structure.find_in_definition(response, '.house-info div', 'Type woning')
        volume = Extractor.volume(Structure.find_in_definition(response, '.house-info div', 'Woonoppervlak'))
        rooms = Structure.find_in_definition(response, '.house-info div', 'Aantal kamers')
        price = Extractor.euro(response, '.house-info div:nth-child(2)')
        availability = Structure.find_in_definition(response, '#tab-1 tr td', 'Aanvaarding')

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
            'estateAgent': 'Eervast',
            'images': Extractor.images(response, '.tab-content > a.gallery::attr(href)', True),
        }


class Nederwoon(scrapy.Spider):
    name = 'nederwoonspider'
    allowed_domains = ["www.nederwoon.nl"]

    def __init__(self, queryRegion='amersfoort'):
        self.region = queryRegion.title()
        self.start_urls = ['http://www.nederwoon.nl/huurwoningen/{0}'.format(queryRegion)]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.location')
        objects.getall()

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
            'estateAgent': 'NederWoon',
            'images': Extractor.images(response, '.slider.slider-media > div img::attr(estate_crawler)'),
        }


class Rotsvast(scrapy.Spider):
    name = 'Rotsvast'
    allowed_domains = ["www.rotsvast.nl"]

    def __init__(self, queryRegion='amersfoort'):
        self.region = queryRegion.title()
        self.start_urls = [
            'https://www.rotsvast.nl/woningaanbod/?type=2&city={0}&type1[]=Appartement&type1[]=Woonhuis&display=list&count=60'.format(
                queryRegion)]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.residence-list.clickable-parent')
        objects.getall()

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
            'images': Extractor.images(response, '.slider img::attr(estate_crawler)', True),
        }


class VanderHulst(scrapy.Spider):
    name = 'van der Hulst'
    allowed_domains = ["vanderhulstverhuurmakelaar.nl"]

    def __init__(self, queryRegion='amersfoort'):
        self.region = queryRegion.title()
        self.start_urls = ['https://vanderhulstverhuurmakelaar.nl/location/{0}/'.format(queryRegion)]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('article.property')
        objects.getall()

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
