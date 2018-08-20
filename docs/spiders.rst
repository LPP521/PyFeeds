.. _Supported Websites:

Supported Websites
==================
Feeds is currently able to create full text Atom feeds for the following websites:

Most popular sites
------------------

.. toctree::
   :maxdepth: 1

   spiders/arstechnica.com
   spiders/facebook.com
   spiders/indiehackers.com
   spiders/lwn.net
   spiders/vice.com

Complete list
-------------
.. toctree::
   :maxdepth: 1
   :glob:

   spiders/*

Some sites (:ref:`Falter <spider_falter.at>`, :ref:`Konsument
<spider_konsument.at>`, :ref:`LWN <spider_lwn.net>`) offer articles only
behind a paywall. If you have a paid subscription, you can configure your
username and password in ``feeds.cfg`` and also read paywalled articles from
within your feed reader.  For the less fortunate who don't have a
subscription, paywalled articles are tagged with ``paywalled`` so they can be
filtered, if desired.

All feeds contain the articles in full text so you never have to leave your
feed reader while reading.
