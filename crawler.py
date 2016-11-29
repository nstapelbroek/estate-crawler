#!/usr/bin/env python
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapper.spider.domica import DomicaSpider
from scrapper.spider.eervast import EervastSpider
from scrapper.spider.nederwoon import NederwoonSpider

configure_logging()
settings = get_project_settings()
settings.set('FEED_FORMAT', 'jsonlines')
settings.set('FEED_URI', 'build/result.json')
runner = CrawlerRunner(settings)

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(DomicaSpider)
    yield runner.crawl(EervastSpider)
    yield runner.crawl(NederwoonSpider)
    reactor.stop()

crawl()
reactor.run()