#!/usr/bin/python3

import uuid

from scrapy import signals
from scrapy.exceptions import DropItem

from feeds.exporters import AtomExporter


class AtomAutogenerateIdPipeline(object):
    """Autogenerate the id field in case it is missing."""
    def process_item(self, item, spider):
        if 'id' in item:
            return item
        else:
            if 'link' in item:
                item['id'] = uuid.uuid5(uuid.NAMESPACE_DNS, item['link']).urn
                return item
            else:
                raise DropItem('A link is required to autogenerate the feed '
                               'id for: {}'.format(item))


class AtomCheckRequiredFieldsPipeline(object):
    """Check presence of required fields."""
    def process_item(self, item, spider):
        for required in ('id', 'title', 'link'):
            if required in item:
                return item
            else:
                raise DropItem('The required field "{}" is missing in: {}.'.
                               format(required, item))


class AtomExportPipeline(object):
    """Export items as atom feeds."""
    def __init__(self, output_path):
        self._output_path = output_path
        self._exporters = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(
            output_path=crawler.settings.get('ATOM_OUTPUT_PATH', 'output'),
        )
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self._exporters[spider] = AtomExporter(self._output_path, spider.name)
        self._exporters[spider].start_exporting()

    def spider_closed(self, spider):
        self._exporters[spider].finish_exporting()
        self._exporters.pop(spider)

    def process_item(self, item, spider):
        self._exporters[spider].export_item(item)
        return item

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
