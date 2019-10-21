# coding=utf-8
from scrapy.selector import Selector
from scrapy.http.response.html import HtmlResponse
from htmllaundry import strip_markup
from urllib.parse import urlparse


class Structure:
    @staticmethod
    def find_in_definition(html, target_element, target_text, index_offset=1) -> str:
        if not isinstance(html, Selector):
            html = Selector(text=html)

        matchedIndex = "not found"
        elements = html.css(target_element)
        elements.getall()

        for index, element in enumerate(elements):
            text = Extractor.string(element)
            if index == matchedIndex:
                return text

            if text.lower() == target_text.lower():
                matchedIndex = index + index_offset

        return str("")


class Extractor:
    @staticmethod
    def euro(html, css_selector="*") -> float:
        data = Extractor.string(html, css_selector)

        # Flip dot and comma, remove euro sign
        data = data.replace(".", "").replace(",", ".").replace("€", "")

        # We remove other words
        words = data.strip().split(" ")
        data = words[0]

        # If we created a string ending with a . append a zero so float conversion is predictable
        if data.endswith(".") or not data:
            data += "0"

        return float(data)

    @staticmethod
    def string(html, css_selector="*") -> str:
        if not isinstance(html, Selector):
            html = Selector(text=html)

        data = html.css(css_selector).get()
        if data is None:
            return str("")

        data = strip_markup(data)
        return data.strip()

    @staticmethod
    def volume(html, css_selector="*") -> float:
        string = Extractor.string(html, css_selector)

        # Flip dot and comma, remove square meters from string
        volume_string = string.split("m")[0]
        volume_string = volume_string.replace(".", "").replace(",", ".")

        # If we created a string ending with a . append a zero so float conversion is predictable
        volume_string.strip()
        if volume_string.endswith(".") or not volume_string:
            volume_string += "0"

        return float(volume_string)

    @staticmethod
    def images(response, css_selector, prefix=None) -> []:
        images = []

        for index, href in enumerate(response.css(css_selector).getall()):
            if isinstance(prefix, str):
                href = prefix + href

            images.append({"href": str(href)})

        return images

    @staticmethod
    def url(response, html, css_selector) -> str:
        path = Extractor.string(html, css_selector)
        parsed_uri = urlparse(response.url)
        domain = "{uri.scheme}://{uri.netloc}".format(uri=parsed_uri)
        return domain + path

    @staticmethod
    def urlWithoutQueryString(response) -> str:
        if not isinstance(response, HtmlResponse):
            raise ValueError("Argument 1 passed into 'urlWithoutQueryString' should be of the type HtmlResponse")

        parsed_reference = urlparse(response.url)
        return parsed_reference.scheme + "://" + parsed_reference.netloc + parsed_reference.path
