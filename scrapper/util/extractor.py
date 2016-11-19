# coding=utf-8
from scrapy.selector import Selector
from htmllaundry import strip_markup


class Extractor:
    @staticmethod
    def euro(html, cssSelector='*'):
        data = Extractor.string(html, cssSelector)
        data = data.replace('.', '').replace(',', '.').replace('€', '')
        return float(data)

    @staticmethod
    def string(html, cssSelector='*'):
        if isinstance(html, str):
            return strip_markup(html).strip()

        if not isinstance(html, Selector):
            html = Selector(html)

        data = html.css(cssSelector).extract_first()
        if data is None:
            return str('')

        data = str(strip_markup(data).encode('utf-8'))
        return data.strip()

    @staticmethod
    def volume(html, cssSelector='*'):
        string = Extractor.string(html, cssSelector)
        return string.split('m')[0]
