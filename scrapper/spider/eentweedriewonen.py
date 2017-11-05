# coding=utf-8
import scrapy
from scrapy.selector import Selector, SelectorList
from scrapper.util.extractor import Extractor
from scrapper.util.structure import Structure


class EenTweeDrieWonenSpider(scrapy.Spider):
    name = '123WonenSpider'
    allowed_domains = ["www.123wonen.nl"]

    def __init__(self, queryRegion='Amersfoort'):
        self.region = queryRegion.title()
        self.start_urls = [
            (
                'https://www.123wonen.nl/aanbod?city={0}&radius=10&min_price=&max_price=&size_m2=&per-page=50'
                .format(queryRegion)
            )
        ]

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.residence-item')
        objects.extract()

        for index, object in enumerate(objects):
            # Determine if the object is still available for rent
            objectStatus = str(Extractor.string(object, '.status-label')).lower()
            if objectStatus in ['verhuurd', 'in optie']:
                continue

            # Skip crawling storage spaces and garages
            type = Structure.find_in_definition(object, '.offer-detail > *', 'Type').lower()
            if type in ['Garagebox', 'Berging/Opslag', 'Kantoorruimte', 'Loods', 'Parkeerplaats', 'Winkelpand']:
                continue

            yield scrapy.Request(Extractor.url(response, object, '.button.button-orange::attr(href)'), self.parse_object)

    def parse_object(self, response):
        city_heading = Extractor.string(response, '.offer-detail-city').split(',')
        city = Extractor.string(city_heading[0])

        # The site adds (nieuw) to a streetname whenever the object is considered new.
        street_heading = Extractor.string(response, '.offer-detail-street').split('(nieuw)')
        street = Extractor.string(street_heading[0])

        volume = Structure.find_in_definition(response, '.offer-detail-container .offer-detail > *', 'Woonoppervlakte')
        if volume is not None and isinstance(volume, basestring):
            volume = Extractor.volume(volume)

        rooms = Structure.find_in_definition(response, '.offer-detail-container .offer-detail > *', 'Slaapkamers')
        if rooms is not None and isinstance(rooms, basestring):
            Extractor.string(rooms)

        type = Structure.find_in_definition(response, '.offer-detail-container .offer-detail > *', 'Type')
        if type is not None and isinstance(type, basestring):
            Extractor.string(type)

        price = Structure.find_in_definition(response, '.offer-detail-container .offer-detail > *', 'Huurprijs')
        if price is not None and isinstance(type, basestring):
            price = Extractor.euro(price)

        # If the object is available for rental right now, the site will give a DT without matching DD
        right_now_element = response.xpath("//dt[@class='offer-value'][contains(text(),'Per direct beschikbaar')]")
        if isinstance(right_now_element, SelectorList) and len(right_now_element) > 0:
            availability = 'Per Direct'
        else:
            availability = Structure.find_in_definition(
                response,
                '.offer-detail-container .offer-detail > *',
                'Beschikbaar vanaf'
            )
            if availability is not None and isinstance(type, basestring):
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
            'images': Extractor.images(response, '.highslide-gallery > a::attr(href)', True, 'https:'),
        }
