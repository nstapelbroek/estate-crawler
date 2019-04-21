# coding=utf-8
import re
import scrapy

from scrapy.exceptions import NotSupported
from scrapy.selector import Selector
from scrapy.http import FormRequest
from estate_crawler.util import Extractor, Structure

ignored_object_types = ['garagebox', 'berging/opslag', 'kantoorruimte', 'loods', 'parkeerplaats', 'winkelpand']
ignored_object_statuses = ['verhuurd', 'in optie', 'onder optie']

class Domica(scrapy.Spider):
    name = 'domicaspider'
    allowed_domains = ['domica.nl', 'www.domica.nl', 'domicasoftware.nl', 'www.domicasoftware.nl']

    def __init__(self, queryRegion='Amersfoort'):
        self.region = queryRegion.title()
        self.start_urls = [
            (
                f'https://domica.nl/huren/plaatsnaam-{queryRegion}'
            )
        ]

    def parse(self, response):
        page_selector = Selector(response)
        objects = page_selector.css('.result-container .product-row').getall()

        for _, object in enumerate(objects):
            object_status = Extractor.string(object, '.images > .product-label').lower()
            if object_status in ignored_object_statuses:
                continue

            object_type = Structure.find_in_definition(object, '.more-info .info > *', 'Objecttype').lower()
            if object_type in ignored_object_types:
                continue

            rooms = Extractor.string(object, '.properties > .property')
            object_url = Extractor.url(response, object, '.images a[rel="click"]::attr(href)')
            yield scrapy.Request(object_url, self.parse_object, meta={'rooms': rooms})

    def parse_object(self, response):
        page_selector = Selector(response=response)
        street = Structure.find_in_definition(page_selector, '.table-specs tr td', 'Straat')
        city = Structure.find_in_definition(page_selector, '.table-specs tr td', 'Plaatsnaam')
        volume = Structure.find_in_definition(page_selector, '.table-specs tr td', 'Oppervlakte')
        type = Structure.find_in_definition(page_selector, '.table-specs tr td', 'Type object')
        price = Structure.find_in_definition(page_selector, '.table-specs tr td', 'Kale huurprijs')
        service_costs = Structure.find_in_definition(page_selector, '.table-specs tr td', 'Servicekosten')
        availability = Extractor.string(page_selector, '.availability strong')
        if volume:
            volume = Extractor.volume(volume)

        price = Extractor.euro(price)
        if service_costs:
            price = price + Extractor.euro(service_costs)

        yield {
            'street': street,
            'city': city,
            'region': self.region,
            'volume': volume,
            'rooms': response.meta['rooms'],
            'availability': availability,
            'type': type,
            'pricePerMonth': price,
            'reference': Extractor.urlWithoutQueryString(response),
            'estateAgent': 'Domica',
            'images': Extractor.images(page_selector, 'a[data-fancybox="gallery"]::attr(href)', True),
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
            object_status = str(Extractor.string(object, '.pand-status')).lower()
            if object_status in ignored_object_statuses :
                continue

            type = Structure.find_in_definition(object, '.pand-specs li > span', 'Type').lower()
            if type in ignored_object_types:
                continue

            yield scrapy.Request(
                Extractor.string(object, 'a.textlink-design:contains("Details")::attr(href)'),
                self.parse_object
            )

        nextPageSelector = '.productBrowser a:contains("volgende")'
        nextPageLink = pageSelector.css(nextPageSelector).get()
        if nextPageLink is not None and isinstance(nextPageLink, str):
            nextPageSelector += '::attr(href)'
            yield scrapy.Request(
                Extractor.url(response, pageSelector, nextPageSelector),
                self.parse,
            )

    def parse_object(self, response):
        page_selector = Selector(response=response)
        breadCrumbTitle = Extractor.string(page_selector, 'a.active span').split(' - ')
        city = Extractor.string(breadCrumbTitle[0])
        breadCrumbTitle.pop(0)
        street = ' - '.join(breadCrumbTitle)

        volume = Structure.find_in_definition(page_selector, '.pand-specs.panddetail-desc li > span', 'Woonoppervlakte')
        if volume is not None and isinstance(volume, str):
            volume = Extractor.volume(volume)

        rooms = Structure.find_in_definition(page_selector, '.pand-specs.panddetail-desc li > span', 'Kamers')
        if rooms is not None and isinstance(rooms, str):
            Extractor.string(rooms)

        type = Structure.find_in_definition(page_selector, '.pand-specs.panddetail-desc li > span', 'Type')
        if type is not None and isinstance(type, str):
            Extractor.string(type)

        price = Extractor.string(page_selector, '.panddetail-price')
        price = price.split('-')[0]
        price = Extractor.euro(price)

        availability = Structure.find_in_definition(page_selector, '.pand-specs.panddetail-desc li > span',
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
            'images': Extractor.images(page_selector, 'a[data-fancybox="group1"]::attr(href)', True),
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
        page_selector = Selector(response=response)
        type = Structure.find_in_definition(page_selector, '.house-info div', 'Type woning')
        volume = Extractor.volume(Structure.find_in_definition(page_selector, '.house-info div', 'Woonoppervlak'))
        rooms = Structure.find_in_definition(page_selector, '.house-info div', 'Aantal kamers')
        price = Extractor.euro(page_selector, '.house-info div:nth-child(2)')
        availability = Structure.find_in_definition(page_selector, '#tab-1 tr td', 'Aanvaarding')

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
            'images': Extractor.images(page_selector, '.tab-content > a.gallery::attr(href)', True),
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
        page_selector = Selector(response=response)
        street = Extractor.string(page_selector, 'h1.text-regular')
        city = Extractor.string(page_selector, '.col-md-8 .fixed-lh p.color-medium')
        availability = Extractor.string(page_selector, '.col-md-8 .horizontal-items ul li:last-child')

        # Sometimes Nederwoon mistakenly adds the zip code in the city field, filter it out
        city = re.sub('\d{4}?\s*[a-zA-Z]{2}', '', city).replace(' ', '')

        rooms = Extractor.string(
            Structure.find_in_definition(page_selector, '.table-striped.table-specs td', 'Aantal kamers')
        )
        price = Extractor.euro(
            Structure.find_in_definition(page_selector, '.table-striped.table-specs td', 'Totale huur per maand', 2)
        )
        volume = Extractor.volume(
            Structure.find_in_definition(page_selector, '.table-striped.table-specs td', 'Woonoppervlakte')
        )
        type = Extractor.string(
            Structure.find_in_definition(page_selector, '.table-striped.table-specs td', 'Soort woonruimte')
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
            'images': Extractor.images(page_selector, '.slider.slider-media > div img::attr(estate_crawler)'),
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
        page_selector = Selector(response=response)
        availability = Extractor.string(
            Structure.find_in_definition(page_selector, '#properties .row > .col-xs-6', 'Ingangsdatum')
        )
        rooms = Extractor.string(
            Structure.find_in_definition(page_selector, '#properties .row > .col-xs-6', 'Aantal kamers')
        )
        price = Extractor.euro(
            Structure.find_in_definition(page_selector, '#properties .row > .col-xs-6', 'Totale huur').split('-')[0]
        )
        volume = Extractor.volume(
            Structure.find_in_definition(page_selector, '#properties .row > .col-xs-6', 'Oppervlakte (ca.)')
        )
        type = Extractor.string(
            Structure.find_in_definition(page_selector, '#properties .row > .col-xs-6', 'Soort')
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
            'images': Extractor.images(page_selector, '.slider img::attr(estate_crawler)', True),
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
            object_status = str(Extractor.string(object, '.property-row-meta-item-status > strong')).lower()
            if object_status in ignored_object_statuses:
                continue

            objectUrl = Extractor.string(object, 'a.property-row-image::attr(href)')
            yield scrapy.Request(objectUrl, self.parse_object)

    def parse_object(self, response):
        page_selector = Selector(response=response)
        tableSelector = '.property-overview dl > *'

        yield {
            'street': Extractor.string(page_selector, 'h1.entry-title'),
            'city': Extractor.string(Structure.find_in_definition(page_selector, tableSelector, 'Plaats')).title(),
            'region': self.region,
            'volume': Extractor.volume(Structure.find_in_definition(page_selector, tableSelector, 'Woonoppervlakte')),
            'rooms': Extractor.string(Structure.find_in_definition(page_selector, tableSelector, 'Kamers')),
            'availability': Extractor.string(Structure.find_in_definition(page_selector, tableSelector, 'Status')),
            'type': Extractor.string(Structure.find_in_definition(page_selector, tableSelector, 'Type')),
            'pricePerMonth': Extractor.euro(Structure.find_in_definition(page_selector, tableSelector, 'Prijs')),
            'reference': Extractor.urlWithoutQueryString(response),
            'estateAgent': 'Van der Hulst',
            'images': Extractor.images(page_selector, '.property-detail-gallery a::attr(href)', True),
        }
