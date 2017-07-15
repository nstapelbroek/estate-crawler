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
settings.set('BOT_NAME', 'estate-crawler')
settings.set('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36')
settings.set('CONCURRENT_REQUESTS', '8')
settings.set('CONCURRENT_REQUESTS_PER_DOMAIN', '3')
settings.set('FEED_FORMAT', 'jsonlines')
settings.set('FEED_URI', 'build/result.json')
settings.set('COOKIES_ENABLED', False)

# Want to send your crawler results to an external API? uncomment these lines below
# settings.set('ITEM_PIPELINES', {'scrapper.pipeline.api.Api': 300})
# settings.set('SCRAPPER_API_URL', 'https://your-api-endpoint.com')

runner = CrawlerRunner(settings)

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(EervastSpider)
    yield runner.crawl(DomicaSpider, queryCity='Amersfoort')
    yield runner.crawl(DomicaSpider, queryCity='Arnhem')
    yield runner.crawl(NederwoonSpider, queryCity='Amersfoort')
    yield runner.crawl(NederwoonSpider, queryCity='Arnhem')
    reactor.stop()


crawl()
reactor.run()
