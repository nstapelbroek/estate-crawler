# coding=utf-8
from scrapy.selector import Selector
from htmllaundry import strip_markup


class Extractor:
    @staticmethod
    def eurosAsFloat(html, cssSelector):
        data = Extractor.string(html, cssSelector)
        data = data.replace('.', '').replace(',', '.').replace('€', '')
        return float(data)

    @staticmethod
    def string(html, cssSelector):
        if not isinstance(html, Selector):
            html = Selector(html)

        data = html.css(cssSelector).extract_first()
        data = str(strip_markup(data).encode('utf-8'))
        return data.strip()
