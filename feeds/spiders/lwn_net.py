import re
from datetime import datetime, timedelta, timezone

import scrapy
from dateutil.parser import parse as dateutil_parse
from scrapy.loader.processors import TakeFirst

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


def _remove_empty_headings(text, level=1):
    """
    Recursively remove headings that are not followed by text.
    """
    if not text:
        return

    heading = '<p class="Cat{}HL">'.format(level)
    # Include text of current heading.
    text_new = [text.split(heading)[0]]
    for content in _split_categories(text, heading):
        # Append text of subheadings.
        content = _remove_empty_headings(content, level + 1)
        if content:
            text_new.append(content)
    text = "".join(text_new)

    # Check if text contains content, i.e. not only a heading or tags.
    content = re.sub(r'<p class="Cat\dHL">[^<]+</p>', "", text)
    content = re.sub(r"</?[^>]*>", "", content).strip()
    if not content:
        return None

    return text


def _split_categories(text, heading):
    """
    Splits the text along the given heading. Text before the first heading is
    ignored. The yielded text includes the heading.
    """
    text_new = []
    after_heading = False
    for line in text.splitlines(True):
        if heading in line:
            if after_heading:
                # New heading detected. Yield what we found until now.
                yield "".join(text_new)
                text_new = []
            else:
                # New heading detected and it's the first one.
                after_heading = True
        if after_heading:
            text_new.append(line)
    yield "".join(text_new)


class LwnNetSpider(FeedsXMLFeedSpider):
    name = "lwn.net"
    allowed_domains = ["lwn.net"]
    namespaces = [
        ("dc", "http://purl.org/dc/elements/1.1/"),
        # Default (empty) namespaces are not supported so we just come up with
        # one.
        ("rss", "http://purl.org/rss/1.0/"),
    ]
    itertag = "rss:item"
    # Use XML iterator instead of regex magic which would fail due to the
    # introduced rss namespace prefix.
    iterator = "xml"
    # lwn.net doesn't like it (i.e. blocks us) if we impose too much load.
    custom_settings = {"DOWNLOAD_DELAY": 1.0}

    _subscribed = False
    # Only scrape articles from the last 7 days.
    # This should be enough since articles are cached by a feed reader anyway.
    _num_days = 7

    def start_requests(self):
        username = self.spider_settings.get("username")
        password = self.spider_settings.get("password")
        if username and password:
            yield scrapy.FormRequest(
                url="https://{}/login".format(self.name),
                formdata={
                    "Username": username,
                    "Password": password,
                    "target": "/MyAccount/",
                    "submit": "Log+in",
                },
                callback=self._after_login,
                meta={"dont_cache": True},
            )
        else:
            # Username, password or section not found in feeds.cfg.
            self.logger.info(
                "Login failed: No username or password given. "
                "Only free articles are available in full text."
            )
            yield self._start_requests()

    def _after_login(self, response):
        error = response.css(".ErrorMessage::text").extract_first()
        if error:
            self.logger.error("Login failed: {}".format(error))
        else:
            text = "".join(response.css(".ArticleText ::text").extract())
            self._subscribed = "You are currently subscribed" in text
            if not self._subscribed:
                self.logger.warning("You are not subscribed to LWN.net")
        yield self._start_requests()

    def _start_requests(self):
        return scrapy.Request(
            "https://{}/headlines/rss".format(self.name),
            self.parse,
            meta={"dont_cache": True},
        )

    def parse_node(self, response, node):
        il = FeedEntryItemLoader(
            response=response, base_url="https://{}".format(self.name), dayfirst=False
        )
        updated = node.xpath("dc:date/text()").extract_first()
        if dateutil_parse(updated) + timedelta(days=self._num_days) < datetime.now(
            timezone.utc
        ):
            self.logger.debug(
                ("Skipping item from {} since older than {} " "days").format(
                    updated, self._num_days
                )
            )
            return
        il.add_value("updated", updated)
        title = node.xpath("rss:title/text()").extract_first()
        paywalled = title.startswith("[$]")
        if paywalled:
            title = title.replace("[$] ", "")
            il.add_value("category", "paywalled")
        link = node.xpath("rss:link/text()").extract_first()
        link = link.replace("rss", "")
        link = link.replace("http://", "https://")
        meta = {"il": il}
        if paywalled and not self._subscribed:
            il.add_value("title", title)
            il.add_value("author_name", node.xpath("dc:creator/text()").extract_first())
            il.add_value(
                "content_text", node.xpath("rss:description/text()").extract_first()
            )
            il.add_value("link", link)
            yield il.load_item()
        else:
            if "LWN.net Weekly Edition for" in title:
                meta["updated"] = updated
                callback = self._parse_weekly_edition
                link += "bigpage"
            else:
                callback = self._parse_article
            # Don't include link yet, we will use the subscriber link later.
            # So subscriber articles can be shared from the feed reader and
            # read in browser without logging in.
            yield scrapy.Request(link, callback, meta=meta)

    def _parse_article(self, response):
        remove_elems = [
            ".FeatureByline",
            ".GAByline",
            ".Form",
            "form",
            ".MakeALink",
            "br",
        ]
        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            remove_elems=remove_elems,
            base_url="https://{}".format(self.name),
            dayfirst=True,
        )
        text = response.css(".ArticleText").extract_first()
        # Remove 'Log in to post comments'.
        text = re.sub(
            r'<hr width="60%" align="left">.*to post comments\)', "", text, flags=re.S
        )
        il.add_css("title", "h1::text")
        il.add_value("content_html", text)
        il.add_css("author_name", ".FeatureByline b ::text")
        il.add_xpath(
            "updated",
            '//div[@class="FeatureByline"]/text()[preceding-sibling::br]',
            TakeFirst(),
        )
        il.add_xpath("updated", '//div[@class="GAByline"]/p[1]/text()')
        # Last resort if date cannot be extracted and it's a weekly edition.
        if "updated" in response.meta:
            il.add_value("updated", response.meta["updated"])
        if response.css(".MakeALink"):
            # Get subscriber link for paywalled content.
            yield scrapy.FormRequest.from_response(
                response,
                formcss=".MakeALink form",
                callback=self._subscriber_link,
                meta={"il": il},
            )
        else:
            il.add_value("link", response.url)
            yield il.load_item()

    def _subscriber_link(self, response):
        il = response.meta["il"]
        link = response.css(".ArticleText li a::attr(href)").extract_first()
        il.add_value("link", link)
        yield il.load_item()

    def _parse_weekly_edition(self, response):
        remove_elems = ["h1"]
        change_tags = {
            ".Cat1HL": "h1",
            ".Cat2HL": "h2",
            ".Cat3HL": "h3",
            ".SummaryHL": "h4",
        }
        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            change_tags=change_tags,
            remove_elems=remove_elems,
            base_url="https://{}".format(self.name),
        )

        for url in response.css("h2.SummaryHL a::attr(href)").extract():
            yield scrapy.Request(
                response.urljoin(url),
                self._parse_article,
                meta={"il": None, "updated": response.meta["updated"]},
            )

        # Remove articles that have their own page.
        text = []
        in_article = False
        for line in response.css(".ArticleText").extract_first().splitlines(True):
            # Beginning of article.
            if '<h2 class="SummaryHL"><a href="/Articles/' in line:
                in_article = True
            if not in_article:
                text.append(line)
            # End of article. Note that the links to the comments doesn't
            # always include "#comments" so we can't check for that.
            if '">Comments (' in line:
                in_article = False
        text = "".join(text)

        # Remove page editor.
        text = re.sub(r"<b>Page editor</b>: .*", "", text)

        # Recursively remove headings with no content.
        text = _remove_empty_headings(text)

        il.add_css("title", "h1::text")
        il.add_value("content_html", text)
        il.add_value("link", response.url)
        yield il.load_item()
