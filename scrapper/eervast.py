# coding=utf-8
import scrapy
from urlparse import urlparse
from scrapy.selector import Selector
from util.extractor import Extractor
from scrapy.http import FormRequest

'''
Eervast is an Amersfoort specific real estate agency, no queryCity parameter will be used

Instead of calling a GET to a page, Eervast requires a POST to an endpoint that will filter out apartments and houses
type mappings: 0 = No preference, 1 = house, 4 = apartment, 10 = room, 20 = studio, 21 = chalet, 22 = attic/upper house
beschikbaarheid mappings: 0 = No preference, 1 = immediately, 2 = within two months, 3 = within 6 months, 4 = after six months
inrichting mappings: 0 = No preference, 1 = furnished, 2 = partly furnished, 3 = bare
ordering mappings: 3 = NO preference, 1 = lowest price, 2 = highest price
prijs_van = lower limit price in int
prijs_tot = upper limit price in int
'''


class EervastSpider(scrapy.Spider):
    name = 'eervastspider'
    allowed_domains = ["www.eervast.nl"]

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
        types = ['4', '20']  # Initially only look for apartments and studios
        requests = []
        for type in types:
            requests.append(self.build_request(type))
        return requests

    def parse(self, response):
        pageSelector = Selector(response)
        objects = pageSelector.css('.home-house')
        objects.extract()

        for index, object in enumerate(objects):
            # Parse Path and send another request
            path = object.css('.house-button a').re_first(r'href="\s*(.*)\"')
            parsed_uri = urlparse(response.url)
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

            # Extracting the street is a lot easier in the overview page, so we'll pass it into the meta
            street = Extractor.string(object, '.home-house-info h2')
            city = Extractor.string(object, '.home-house-info h3').split(" ")
            city = city[len(city) - 1]
            meta = {'street': street, 'city': city}
            yield scrapy.Request(domain + path, self.parse_object, 'GET', None, None, None, meta)

    # The eervast pages are build like a defintion list usign divs or tables.
    # By picking the next sibling element of the matched content we can extract specific information
    def find_in_defintion_elements(self, html, targetElement, targetText):
        if not isinstance(html, Selector):
            html = Selector(html)

        matchedIndex = 'not found'
        elements = html.css(targetElement)
        elements.extract()

        for index, element in enumerate(elements):
            text = Extractor.string(element, '*');
            if index == matchedIndex:
                return text

            if text.lower() == targetText.lower():
                matchedIndex = index + 1

    def parse_object(self, response):
        type = self.find_in_defintion_elements(response, '.house-info div', 'Type woning')
        volume = self.find_in_defintion_elements(response, '.house-info div', 'Woonoppervlak').split('m')[0]
        rooms = self.find_in_defintion_elements(response, '.house-info div', 'Aantal kamers')
        price = Extractor.eurosAsFloat(response, '.house-info div:nth-child(2)')
        availability = self.find_in_defintion_elements(response, '#tab-1 tr td', 'Aanvaarding')

        yield {
            'street': response.meta['street'],
            'city': response.meta['city'],
            'volume': volume,
            'rooms': rooms,
            'availability': availability,
            'type': type,
            'price': price,
            'reference': response.url
        }
