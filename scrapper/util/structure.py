# coding=utf-8
from scrapy.selector import Selector
from scrapper.util.extractor import Extractor


class Structure:
    @staticmethod
    def find_in_definition(html, targetElement, targetText, indexOffset = 1):
        if not isinstance(html, Selector):
            html = Selector(html)

        matchedIndex = 'not found'
        elements = html.css(targetElement)
        elements.extract()

        for index, element in enumerate(elements):
            text = Extractor.string(element)
            if index == matchedIndex:
                return text

            if text.lower() == targetText.lower():
                matchedIndex = index + indexOffset
