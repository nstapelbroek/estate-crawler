# coding=utf-8
import re
from abc import ABC

import scrapy

from scrapy.selector import Selector
from scrapy.http import FormRequest
from estate_crawler.util import Extractor, Structure

ignored_object_types = ["garagebox", "berging/opslag", "kantoorruimte", "loods", "parkeerplaats", "winkelpand"]
ignored_object_statuses = ["verhuurd", "in optie", "onder optie"]


class Spider(scrapy.Spider, ABC):
    name = "unknown"
    allowed_domains = []
    query_region = ""

    def __init__(self, query_region="Amersfoort"):
        super().__init__()
        self.query_region = query_region.title()


class Domica(Spider):
    name = "domicaspider"
    allowed_domains = ["domica.nl", "www.domica.nl", "domicasoftware.nl", "www.domicasoftware.nl"]

    @property
    def start_urls(self) -> list:
        return [f"https://domica.nl/huren/plaatsnaam-{self.query_region}"]

    def parse(self, response):
        page_selector = Selector(response)
        objects = page_selector.css(".result-container .product-row").getall()

        for _, estate_object in enumerate(objects):
            object_status = Extractor.string(estate_object, ".images > .product-label").lower()
            if object_status in ignored_object_statuses:
                continue

            object_type = Structure.find_in_definition(estate_object, ".more-info .info > *", "Objecttype").lower()
            if object_type in ignored_object_types:
                continue

            # Rooms is only given on the overview page
            rooms = Extractor.string(estate_object, ".properties > .property")
            object_url = Extractor.url(response, estate_object, '.images a[rel="click"]::attr(href)')
            yield scrapy.Request(object_url, self.parse_object, meta={"rooms": rooms})

    def parse_object(self, response):
        page_selector = Selector(response=response)
        street = Structure.find_in_definition(page_selector, ".table-specs tr td", "Straat")
        city = Structure.find_in_definition(page_selector, ".table-specs tr td", "Plaatsnaam")
        volume = Structure.find_in_definition(page_selector, ".table-specs tr td", "Oppervlakte")
        object_type = Structure.find_in_definition(page_selector, ".table-specs tr td", "Type object")
        price = Structure.find_in_definition(page_selector, ".table-specs tr td", "Kale huurprijs")
        service_costs = Structure.find_in_definition(page_selector, ".table-specs tr td", "Servicekosten")
        availability = Extractor.string(page_selector, ".availability strong")
        if volume:
            volume = Extractor.volume(volume)

        price = Extractor.euro(price)
        if service_costs:
            price = price + Extractor.euro(service_costs)

        yield {
            "street": street,
            "city": city,
            "region": self.query_region,
            "volume": volume,
            "rooms": response.meta["rooms"],
            "availability": availability,
            "type": object_type,
            "pricePerMonth": price,
            "reference": Extractor.urlWithoutQueryString(response),
            "estateAgent": "Domica",
            "images": Extractor.images(page_selector, 'a[data-fancybox="gallery"]::attr(href)', True),
        }


class EenTweeDrieWonen(Spider):
    name = "123WonenSpider"
    allowed_domains = ["www.123wonen.nl", "123wonen.nl"]

    def start_requests(self):
        # 123wonen.nl url's do not determine the content. We'll need to POST our queries
        form_data = {
            "cm01": "1",
            "redirecturl": "huurwoningen",
            "pricerange": "-",
            "city": self.query_region,
            "zipcoder": "0",
            "price_start": "0",
            "price_end": "0",
        }

        return [FormRequest("https://www.123wonen.nl/huurwoningen", formdata=form_data, callback=self.parse)]

    def parse(self, response):
        page_selector = Selector(response)
        objects = page_selector.css(".pandlist-container").getall()

        for _, estate_object in enumerate(objects):
            object_status = str(Extractor.string(estate_object, ".pand-status")).lower()
            if object_status in ignored_object_statuses:
                continue

            object_type = Structure.find_in_definition(estate_object, ".pand-specs li > span", "Type").lower()
            if object_type in ignored_object_types:
                continue

            object_url = Extractor.string(estate_object, 'a.textlink-design:contains("Details")::attr(href)')
            yield scrapy.Request(object_url, self.parse_object)

        next_page_selector = '.productBrowser a:contains("volgende")'
        next_page_link = page_selector.css(next_page_selector).get()
        if next_page_link is not None and isinstance(next_page_link, str):
            next_page_selector += "::attr(href)"
            yield scrapy.Request(Extractor.url(response, page_selector, next_page_selector), self.parse)

    def parse_object(self, response):
        page_selector = Selector(response=response)

        bread_crumb_title = Extractor.string(page_selector, "a.active span").split(" - ")
        city = Extractor.string(bread_crumb_title[0])
        bread_crumb_title.pop(0)
        street = " - ".join(bread_crumb_title)
        price = Extractor.string(page_selector, ".panddetail-price")
        price = price.split("-")[0]
        price = Extractor.euro(price)

        specs_selector = ".pand-specs.panddetail-desc li > span"
        volume = Extractor.volume(Structure.find_in_definition(page_selector, specs_selector, "Woonoppervlakte"))
        rooms = Extractor.string(Structure.find_in_definition(page_selector, specs_selector, "Kamers"))
        object_type = Extractor.string(Structure.find_in_definition(page_selector, specs_selector, "Type"))
        availability = Extractor.string(Structure.find_in_definition(page_selector, specs_selector, "Beschikbaarheid"))

        yield {
            "street": street,
            "city": city,
            "region": self.query_region,
            "volume": volume,
            "rooms": rooms,
            "availability": availability,
            "type": object_type,
            "pricePerMonth": price,
            "reference": Extractor.urlWithoutQueryString(response),
            "estateAgent": "123Wonen.nl",
            "images": Extractor.images(page_selector, 'a[data-fancybox="group1"]::attr(href)', True),
        }


class Eervast(Spider):
    name = "eervastspider"
    allowed_domains = ["www.eervast.nl", "eervast.nl"]

    def _build_initial_post_request(self, type_value):
        base_url = "http://www.eervast.nl/includes/php/huren-search.php"
        form_data = {
            "type": type_value,
            "beschikbaarheid": "0",
            "inrichting": "0",
            "ordering": "3",
            "prijs_van": "0",
            "prijs_tot": "9999",
        }

        return FormRequest(base_url, formdata=form_data, callback=self.parse)

    def start_requests(self):
        if self.query_region.lower() != "amersfoort":
            return []

        types = ["4", "10", "20"]  # Initially only look for apartments and studios
        return [self._build_initial_post_request(t) for t in types]

    def parse(self, response):
        page_selector = Selector(response)
        objects = page_selector.css(".home-house").getall()

        for _, object_type in enumerate(objects):
            object_url = Extractor.url(response, object_type, ".house-button a::attr(href)")

            # Extracting the street is a lot easier in the overview page, so we'll pass it into the meta
            street = Extractor.string(object_type, ".home-house-info h2")
            city = Extractor.string(object_type, ".home-house-info h3").split(" ")
            city = city[len(city) - 1]
            meta = {"street": street, "city": city}
            yield scrapy.Request(object_url, self.parse_object, "GET", None, None, None, meta)

    def parse_object(self, response):
        page_selector = Selector(response=response)
        object_type = Structure.find_in_definition(page_selector, ".house-info div", "Type woning")
        volume = Extractor.volume(Structure.find_in_definition(page_selector, ".house-info div", "Woonoppervlak"))
        rooms = Structure.find_in_definition(page_selector, ".house-info div", "Aantal kamers")
        price = Extractor.euro(page_selector, ".house-info div:nth-child(2)")
        availability = Structure.find_in_definition(page_selector, "#tab-1 tr td", "Aanvaarding")

        yield {
            "street": response.meta["street"],
            "city": response.meta["city"],
            "region": self.query_region,
            "volume": volume,
            "rooms": rooms,
            "availability": availability,
            "type": object_type,
            "pricePerMonth": price,
            "reference": Extractor.urlWithoutQueryString(response),
            "estateAgent": "Eervast",
            "images": Extractor.images(page_selector, ".tab-content > a.gallery::attr(href)", True),
        }


class Nederwoon(Spider):
    name = "nederwoonspider"
    allowed_domains = ["www.nederwoon.nl", "nederwoon.nl"]

    @property
    def start_urls(self) -> list:
        return [f"http://www.nederwoon.nl/huurwoningen/{self.query_region}"]

    def parse(self, response):
        page_selector = Selector(response)
        objects = page_selector.css(".location").getall()

        for _, estate_object in enumerate(objects):
            object_url = Extractor.url(response, estate_object, "h2.heading-sm > a::attr(href)")
            yield scrapy.Request(object_url, self.parse_object)

    def parse_object(self, response):
        page_selector = Selector(response=response)
        street = Extractor.string(page_selector, "h1.text-regular")
        city = Extractor.string(page_selector, ".col-md-8 .fixed-lh p.color-medium")
        availability = Extractor.string(page_selector, ".col-md-8 .horizontal-items ul li:last-child")

        # Sometimes Nederwoon mistakenly adds the zip code in the city field, filter it out
        city = re.sub(r"\d{4}?\s*[a-zA-Z]{2}", "", city).replace(" ", "")

        specs_selector = ".table-striped.table-specs td"
        rooms = Extractor.string(Structure.find_in_definition(page_selector, specs_selector, "Aantal kamers"))
        price = Extractor.euro(Structure.find_in_definition(page_selector, specs_selector, "Totale huur per maand", 2))
        volume = Extractor.volume(Structure.find_in_definition(page_selector, specs_selector, "Woonoppervlakte"))
        object_type = Structure.find_in_definition(page_selector, "%s" % specs_selector, "Soort woonruimte")
        if object_type:
            object_type = Extractor.string(object_type)

        yield {
            "street": street,
            "city": city,
            "region": self.query_region,
            "volume": volume,
            "rooms": rooms,
            "availability": availability,
            "type": object_type,
            "pricePerMonth": price,
            "reference": Extractor.urlWithoutQueryString(response),
            "estateAgent": "NederWoon",
            "images": Extractor.images(page_selector, ".slider.slider-media > div img::attr(estate_crawler)"),
        }


class Rotsvast(Spider):
    name = "Rotsvast"
    allowed_domains = ["www.rotsvast.nl", "rotsvast.nl"]

    @property
    def start_urls(self) -> list:
        default_query_params = "type1[]=Appartement&type1[]=Woonhuis&display=list&count=60"
        return [f"https://www.rotsvast.nl/woningaanbod/?type=2&city={self.query_region}&{default_query_params}"]

    def parse(self, response):
        page_selector = Selector(response)
        objects = page_selector.css(".residence-list.clickable-parent").getall()

        for _, estate_object in enumerate(objects):
            object_url = Extractor.string(estate_object, "a.clickable-block::attr(href)")

            # Extracting the street is a lot easier in the overview page, so we'll pass it into the meta
            street = Extractor.string(estate_object, ".residence-street")
            city = Extractor.string(estate_object, ".residence-zipcode-place").split(" ")[1:]
            city = " ".join(city)
            meta = {"street": street, "city": city}

            yield scrapy.Request(object_url, self.parse_object, "GET", meta=meta)

    def parse_object(self, response):
        page_selector = Selector(response=response)
        specs_selector = "#properties .row > .col-xs-6"
        availability = Extractor.string(Structure.find_in_definition(page_selector, specs_selector, "Ingangsdatum"))
        rooms = Extractor.string(Structure.find_in_definition(page_selector, specs_selector, "Aantal kamers"))
        volume = Extractor.volume(Structure.find_in_definition(page_selector, specs_selector, "Oppervlakte (ca.)"))
        object_type = Extractor.string(Structure.find_in_definition(page_selector, specs_selector, "Soort"))
        price = Structure.find_in_definition(page_selector, specs_selector, "Totale huur").split("-")[0]
        price = Extractor.euro(price)

        yield {
            "street": response.meta["street"],
            "city": response.meta["city"],
            "region": self.query_region,
            "volume": volume,
            "rooms": rooms,
            "availability": availability,
            "type": object_type,
            "pricePerMonth": price,
            "reference": Extractor.urlWithoutQueryString(response),
            "estateAgent": "Rotsvast",
            "images": Extractor.images(page_selector, ".slider img::attr(estate_crawler)", True),
        }


class VanderHulst(Spider):
    name = "van der Hulst"
    allowed_domains = ["vanderhulstverhuurmakelaar.nl", "www.vanderhulstverhuurmakelaar.nl"]

    @property
    def start_urls(self) -> list:
        return [f"https://vanderhulstverhuurmakelaar.nl/location/{self.query_region}/"]

    def parse(self, response):
        page_selector = Selector(response)
        objects = page_selector.css("article.property").getall()

        for _, estate_object in enumerate(objects):
            object_status = str(Extractor.string(estate_object, ".property-row-meta-item-status > strong")).lower()
            if object_status in ignored_object_statuses:
                continue

            object_url = Extractor.string(estate_object, "a.property-row-image::attr(href)")
            yield scrapy.Request(object_url, self.parse_object)

    def parse_object(self, response):
        page_selector = Selector(response=response)
        table_selector = ".property-overview dl > *"

        yield {
            "street": Extractor.string(page_selector, "h1.entry-title"),
            "city": Extractor.string(Structure.find_in_definition(page_selector, table_selector, "Plaats")).title(),
            "region": self.query_region,
            "volume": Extractor.volume(Structure.find_in_definition(page_selector, table_selector, "Woonoppervlakte")),
            "rooms": Extractor.string(Structure.find_in_definition(page_selector, table_selector, "Kamers")),
            "availability": Extractor.string(Structure.find_in_definition(page_selector, table_selector, "Status")),
            "type": Extractor.string(Structure.find_in_definition(page_selector, table_selector, "Type")),
            "pricePerMonth": Extractor.euro(Structure.find_in_definition(page_selector, table_selector, "Prijs")),
            "reference": Extractor.urlWithoutQueryString(response),
            "estateAgent": "Van der Hulst",
            "images": Extractor.images(page_selector, ".property-detail-gallery a::attr(href)", True),
        }
