import re
from urllib.parse import quote_plus as urlquote_plus

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider
from feeds.utils import generate_feed_header


class DiePresseComSpider(FeedsXMLFeedSpider):
    name = "diepresse.com"
    namespaces = [
        ("news", "http://www.google.com/schemas/sitemap-news/0.9"),
        ("rss", "http://www.sitemaps.org/schemas/sitemap/0.9"),
    ]
    itertag = "rss:url"
    iterator = "xml"

    def start_requests(self):
        sections = self.settings.get("FEEDS_SPIDER_DIEPRESSE_COM_SECTIONS")
        if sections:
            self._sections = set(sections.split())
        else:
            self._sections = ["all"]
        yield scrapy.Request(
            "https://diepresse.com/files/sitemaps/news/news-sitemap.xml"
        )

    def feed_headers(self):
        for section in self._sections:
            yield generate_feed_header(
                title="DiePresse.com/{}".format(section),
                link="https://{}".format(self.name),
                path=urlquote_plus(section),
                logo="http://diepresse.com/img/diepresse_250x40.png",
            )

    def parse_node(self, response, node):
        url = node.xpath("rss:loc/text()").extract_first()
        il = FeedEntryItemLoader(selector=node)
        il.add_value("link", url)
        il.add_xpath("title", "news:news/news:title/text()")
        il.add_value(
            "category",
            node.xpath("news:news/news:keywords/text()").extract_first().split(", "),
        )
        il.add_xpath("updated", "news:news/news:publication_date/text()")
        return scrapy.Request(url, self.parse_item, meta={"il": il})

    def parse_item(self, response):
        def _clean_caption(elem):
            if "–" in elem.text:
                # Caption is of the format "text - credit".
                elem.text = re.sub(r"\s*([^–]*).*", r"\1", elem.text)
                return elem
            else:
                # It's just the "credit", remove it.
                return None

        section = response.css(
            'meta[name="kt:section-path"]::attr("content")'
        ).extract_first()[
            1:
        ]  # Skip the first /.
        if section not in self._sections and "all" not in self._sections:
            # Ignore the response as the ressort should not be parsed.
            return

        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            remove_elems=[".ad", ".article-paid"],
            change_tags={".article__lead": "strong"},
            pullup_elems={".zoomable__image--zoomed": 2},
            change_attribs={".zoomable__image--zoomed": {"data-src": "src"}},
            replace_elems={".article__media-caption": _clean_caption},
            base_url="https://www.{}".format(self.name),
        )
        il.add_css(
            "author_name",
            ".article__main .article__author ::text",
            re=re.compile(r"\s*(?:[Vv]on\s*)?(.+)", flags=re.DOTALL),
        )
        il.add_css("content_html", ".article__main .article__media")
        il.add_css(
            "content_html", ".article__main .article__lead"
        )  # change tags to strong
        il.add_css("content_html", ".article__main .article__body")
        if response.css(".article-paid"):
            il.add_value("category", "paywalled")
        il.add_value("category", section.split("/"))
        if "all" in self._sections:
            il.add_value("path", "all")
        if section in self._sections:
            il.add_value("path", urlquote_plus(section))
        return il.load_item()
