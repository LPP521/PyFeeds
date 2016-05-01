#!/usr/bin/python3

import json

from scrapy.spiders import Spider
import pytz
import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.loaders import FeedItemLoader


class Oe1OrfAtSpider(Spider):
    name = 'oe1.orf.at'
    allowed_domains = ['oe1.orf.at']
    start_urls = ['http://oe1.orf.at/programm/konsole/heute']

    _datetime_format = '%d.%m.%Y %H:%M'
    _timezone = pytz.timezone('Europe/Vienna')

    def parse(self, response):
        il = FeedItemLoader()
        il.add_value('title', 'oe1.ORF.at')
        il.add_value('subtitle', 'Ö1 Webradio')
        il.add_value('link', 'http://oe1.orf.at')
        il.add_value('author_name', self.name)
        yield il.load_item()

        # Only scrape today and the last two days. Exclude the last entry
        # (i.e. today) which is the the current response.
        for day in json.loads(response.body_as_unicode())['nav'][-3:-1]:
            self.logger.debug('day: {}'.format(day))
            yield scrapy.Request('http://{}{}'.format(self.name, day['url']),
                                 self.parse_item)

        yield from self.parse_item(response)

    def parse_item(self, response):
        for item in json.loads(response.body_as_unicode())['list']:
            il = FeedEntryItemLoader(response=response,
                                     datetime_format=self._datetime_format,
                                     timezone=self._timezone,
                                     base_url='http://{}'.format(self.name))
            link = 'http://{}{}'.format(
                self.name, item['url_json'].replace('/konsole', ''))
            il.add_value('link', link)
            il.add_value('title', item['title'])
            il.add_value('enclosure_iri', item['url_stream'])
            il.add_value('enclosure_type', 'audio/mpeg')
            il.add_value('updated', '{} {}'.format(item['day_label'],
                                                   item['time']))
            yield scrapy.Request(link, self.parse_item_text, meta={'il': il})

    def parse_item_text(self, response):
        remove_elems = [
            'script', 'object', '.copyright', '.copyright-small', '.hidden',
            '.overlay-7tage', '.overlay-7tage-hover', '.hover-infobar',
            '.overlay-download', '.gallerynav', '.audiolink', '.autor',
            '.outerleft', '.socialmediaArtikel', '.copyright', '.tags', 'h1'
        ]
        il = FeedEntryItemLoader(response=response,
                                 parent=response.meta['il'],
                                 remove_elems=remove_elems,
                                 base_url='http://{}'.format(self.name))
        il.add_xpath('content_html', '(//div[@class="textbox-wide"])[1]')
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
