from datetime import datetime
from datetime import timedelta

import delorean
import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class ProfilAtSpider(FeedsSpider):
    name = 'profil.at'
    allowed_domains = ['profil.at']

    _title = 'PROFIL'
    _subtitle = 'Österreichs unabhängiges Nachrichtenmagazin'
    _timezone = 'Europe/Vienna'
    _max_days = 3

    def start_requests(self):
        start = datetime.utcnow() - timedelta(days=self._max_days - 1)
        for day in delorean.range_daily(start=start, count=self._max_days,
                                        timezone='UTC'):
            yield scrapy.Request(
                'http://{}/archiv/{}'.format(
                    self.name,
                    day.shift(self._timezone).format_datetime('Y/M/d')),
                self.parse_archive_page)

    def parse_archive_page(self, response):
        for link in response.xpath('//h1/a/@href').extract():
            yield scrapy.Request(response.urljoin(link), self.parse_item)

    def parse_item(self, response):
        remove_elems = [
            'aside', 'script', 'h1', '.breadcrumbs', '.author-date',
            '.artikel-social-kommentar', '.bild-copyright',
            '.ressortTitleMobile', '.article-number', '.artikel-kommentarlink'
        ]
        il = FeedEntryItemLoader(response=response,
                                 timezone=self._timezone,
                                 base_url='http://{}'.format(self.name),
                                 remove_elems=remove_elems)
        il.add_value('link', response.url)
        il.add_xpath('author_name', '//a[@rel="author"]/text()')
        il.add_xpath(
            'author_name', 'substring-before(substring-after('
            '(//section[@class="author-date"]/text())[1]'
            ', "Von"), "(")')
        il.add_value('author_name', 'Red.')
        il.add_xpath('title', '//h1/text()')
        il.add_xpath(
            'updated', 'substring-before('
            '//meta[@property="article:published_time"]/@content'
            ', "+")')
        il.add_xpath('content_html', '//article')
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
