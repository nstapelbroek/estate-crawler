# coding=utf-8
from scrapy.selector import Selector
from htmllaundry import strip_markup


class Extractor:
    @staticmethod
    def euro(html, cssSelector='*'):
        data = Extractor.string(html, cssSelector)

        # Flip dot and comma, remove euro sign
        data = data.replace('.', '').replace(',', '.').replace('€', '')

        # We remove other words
        words = data.strip().split(' ')
        data = words[0]

        # If we created a string ending with a . append a zero so float conversion is predictable
        if(data.endswith('.')):
            data += '0'

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

        # Flip dot and comma, remove square meters from string
        volume_string = string.split('m')[0]
        volume_string = volume_string.replace('.', '').replace(',', '.')

        # If we created a string ending with a . append a zero so float conversion is predictable
        volume_string.strip()
        if(volume_string.endswith('.')):
            volume_string += '0'

        return float(volume_string)
