#!/usr/bin/env python
import argparse
from os import getenv
from scrapy.utils.project import get_project_settings
from scrapy.exceptions import NotSupported
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapper.spider.domica import DomicaSpider
from scrapper.spider.eervast import EervastSpider
from scrapper.spider.eentweedriewonen import EenTweeDrieWonenSpider
from scrapper.spider.nederwoon import NederwoonSpider
from scrapper.spider.vanderhulst import VanderHulstSpider

# Cli handler
parser = argparse.ArgumentParser(description='Crawl estate agencies for real-estate objects.')
parser.add_argument('-r', '--region', help='A comma separated string of regions to search', required=True)
parser.add_argument('-o', '--output-file', help='Location where the crawler will write jsonlines output', required=False)
parser.add_argument('-a', '--output-api', help='HTTP url where the crawler will POST the results towards', required=False)
args = parser.parse_args()

# Setup settings
configure_logging()
settings = get_project_settings()
settings.set('BOT_NAME', 'estate-crawler')
settings.set('USER_AGENT', getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3112.50 Safari/537.36'))
settings.set('CONCURRENT_REQUESTS', getenv('CONCURRENT_REQUESTS', '8'))
settings.set('CONCURRENT_REQUESTS_PER_DOMAIN', getenv('CONCURRENT_REQUESTS_PER_DOMAIN', '3'))
settings.set('FEED_FORMAT', getenv('FEED_FORMAT', 'jsonlines'))
settings.set('FEED_URI', (args.output_file if args.output_file else 'build/result.json'))

if args.output_api:
    settings.set('ITEM_PIPELINES', {'scrapper.pipeline.api.Api': 300})
    settings.set('SCRAPPER_API_URL', args.output_api)

# Runtime
runner = CrawlerRunner(settings)

@defer.inlineCallbacks
def crawl(regionArgument):
    regions = regionArgument.split(',')
    for region in regions:
        try:
            yield runner.crawl(EervastSpider, queryRegion=region)
        except NotSupported:
            print 'skipped spider'

        yield runner.crawl(VanderHulstSpider, queryRegion=region)
        yield runner.crawl(DomicaSpider, queryRegion=region)
        yield runner.crawl(NederwoonSpider, queryRegion=region)
        yield runner.crawl(EenTweeDrieWonenSpider, queryRegion=region)


    reactor.stop()


crawl(args.region)
reactor.run()
