#!/usr/bin/env python
import os
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapper.spider.domica import DomicaSpider
from scrapper.spider.eervast import EervastSpider
from scrapper.spider.eentweedriewonen import EenTweeDrieWonenSpider
from scrapper.spider.nederwoon import NederwoonSpider

configure_logging()
settings = get_project_settings()

# Overwrite Generic spider settings trough environment variables
settings.set('BOT_NAME', os.getenv('BOT_NAME', 'estate-crawler'))
settings.set('USER_AGENT', os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3112.50 Safari/537.36'))
settings.set('CONCURRENT_REQUESTS', os.getenv('CONCURRENT_REQUESTS', '8'))
settings.set('CONCURRENT_REQUESTS_PER_DOMAIN', os.getenv('CONCURRENT_REQUESTS_PER_DOMAIN', '3'))
settings.set('FEED_FORMAT', os.getenv('FEED_FORMAT', 'jsonlines'))
settings.set('FEED_URI', os.getenv('FEED_URI', 'build/result.json'))

# Want to send your crawler results to an external API? Set the environment SCRAPPER_API_URL variable
if "SCRAPPER_API_URL" in os.environ:
    settings.set('ITEM_PIPELINES', {'scrapper.pipeline.api.Api': 300})
    settings.set('SCRAPPER_API_URL', os.getenv('SCRAPPER_API_URL'))

runner = CrawlerRunner(settings)

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(EervastSpider)
    yield runner.crawl(DomicaSpider, queryCity='Amersfoort')
    yield runner.crawl(DomicaSpider, queryCity='Amsterdam')
    yield runner.crawl(DomicaSpider, queryCity='Arnhem')
    yield runner.crawl(DomicaSpider, queryCity='Den Haag')
    yield runner.crawl(DomicaSpider, queryCity='Ede')
    yield runner.crawl(DomicaSpider, queryCity='Enschede')
    yield runner.crawl(DomicaSpider, queryCity='Hilversum')
    yield runner.crawl(DomicaSpider, queryCity='Nijmegen')
    yield runner.crawl(DomicaSpider, queryCity='Rotterdam')
    yield runner.crawl(DomicaSpider, queryCity='Utrecht')
    yield runner.crawl(NederwoonSpider, queryCity='Amersfoort')
    yield runner.crawl(NederwoonSpider, queryCity='Amsterdam')
    yield runner.crawl(NederwoonSpider, queryCity='Arnhem')
    yield runner.crawl(NederwoonSpider, queryCity='Den Haag')
    yield runner.crawl(NederwoonSpider, queryCity='Ede')
    yield runner.crawl(NederwoonSpider, queryCity='Enschede')
    yield runner.crawl(NederwoonSpider, queryCity='Hilversum')
    yield runner.crawl(NederwoonSpider, queryCity='Nijmegen')
    yield runner.crawl(NederwoonSpider, queryCity='Rotterdam')
    yield runner.crawl(NederwoonSpider, queryCity='Utrecht')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Amersfoort')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Amsterdam')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Arnhem')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Den Haag')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Ede')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Enschede')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Hilversum')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Nijmegen')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Rotterdam')
    yield runner.crawl(EenTweeDrieWonenSpider, queryCity='Utrecht')
    reactor.stop()


crawl()
reactor.run()
