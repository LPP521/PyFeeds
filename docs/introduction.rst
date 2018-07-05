Introduction
============
About Feeds
-----------
Once upon a time every website offered an RSS feed to keep readers updated
about new articles/blog posts via the users' feed readers. These times are long
gone. The once iconic orange RSS icon has been replaced by "social share"
buttons.

Feeds aims to bring back the good old reading times. It creates Atom feeds for
websites that don't offer them (anymore). It allows you to read new articles of
your favorite websites in your feed reader (e.g. TinyTinyRSS_) even if this is
not officially supported by the website.

Feeds is based on Scrapy_, a framework for extracting data from websites and it
has support for a few websites already, see :ref:`Supported Websites`. It's
easy to add support for new websites. Just take a look at the existing spiders
in ``feeds/spiders`` and feel free to open a :ref:`pull request <Contribute>`!

Related work
------------
* `morss <https://github.com/pictuga/morss>`_ creates feeds, similar to Feeds
  but in "real-time", i.e. on (HTTP) request.
* `Full-Text RSS <https://bitbucket.org/fivefilters/full-text-rss>`_ converts
  feeds to contain the full article and not only a teaser based on heuristics
  and rules. Feeds are converted in "real-time", i.e. on request basis.
* `f43.me <https://github.com/j0k3r/f43.me>`_ converts feeds to contain the
  full article and also improves articles by adding links to the comment
  sections of Hacker News and Reddit. Feeds are converted periodically.
* `python-ftr <https://github.com/1flow/python-ftr>`_ is a library to extract
  content from pages. A partial reimplementation of Full-Text RSS.

Documentation
-------------
Feeds comes with extensive documentation. It is available at
`https://pyfeeds.readthedocs.io <https://pyfeeds.readthedocs.io/en/latest/>`_.

Authors
-------
Feeds is written and maintained by `Florian Preinstorfer <https://nblock.org>`_
and `Lukas Anzinger <https://www.notinventedhere.org>`_.

.. _Scrapy: https://www.scrapy.org
.. _TinyTinyRSS: https://tt-rss.org
