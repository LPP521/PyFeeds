from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsCrawlSpider


class CbirdAtSpider(FeedsCrawlSpider):
    name = "cbird.at"
    allowed_domains = ["cbird.at"]
    start_urls = ["https://cbird.at/hilfe/neu/", "https://cbird.at/impressum"]
    rules = (Rule(LinkExtractor(allow=("hilfe/neu/(\d+)",)), callback="parse_item"),)

    _title = "Neue cbird Versionen"
    _subtitle = "Die neuesten Versionen von cbird."
    _link = start_urls[0]

    def parse_item(self, response):
        il = FeedEntryItemLoader(
            selector=response.xpath('//div[@class="main"]'), timezone="Europe/Vienna"
        )
        il.add_xpath("title", "h1/text()")
        il.add_value("link", response.url)
        il.add_xpath("content_html", "h1/following-sibling::*")
        il.add_value("updated", response.url.rstrip("/").split("/")[-1].split("_")[0])
        il.add_value("author_name", self.name)
        yield il.load_item()

    def parse_imprint(self, response):
        self._author_name = (
            response.xpath('//div[@class="main"]/p/text()').re_first("Firma (.*)")
            or self.name
        )
