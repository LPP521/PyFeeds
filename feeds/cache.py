import logging
import os
import pickle
import shutil
from datetime import datetime, timezone

from scrapy.extensions.httpcache import FilesystemCacheStorage, DummyPolicy
from scrapy.utils.python import to_bytes
from scrapy.utils.request import request_fingerprint

logger = logging.getLogger(__name__)


class FeedsCachePolicy(DummyPolicy):
    def should_cache_response(self, response, request):
        # We cache all responses regardless of HTTP code.
        return True


class FeedsCacheStorage(FilesystemCacheStorage):
    def __init__(self, settings):
        super().__init__(settings)
        # gzip is not supported
        self.use_gzip = False
        self._open = open
        self.ignore_http_codes = [
            int(x) for x in settings.getlist("HTTPCACHE_IGNORE_HTTP_CODES")
        ]

    def retrieve_response(self, spider, request):
        """Return response if present in cache, or None otherwise."""
        metadata = self._read_meta(spider, request)
        if metadata is not None and metadata["status"] in self.ignore_http_codes:
            # ignore cache entry for error responses
            logger.debug("Response for {} not cached".format(request))
            return
        # Retrieve response from cache.
        try:
            return super().retrieve_response(spider, request)
        finally:
            logger.debug("Retrieved response for {} from cache".format(request))

    def store_response(self, spider, request, response):
        """Store the given response in the cache."""
        # Read the old metadata.
        old_metadata = self._read_meta(spider, request)
        # This will overwrite old metadata (if there is one).
        super().store_response(spider, request, response)
        # Read the new metadata.
        metadata = self._read_meta(spider, request)
        # Add the parents' fingerprints to the metadata and merge the parents from the
        # old metadata. The last fingerprint is not included since it's the fingerprint
        # of this request.
        metadata["parents"] = list(
            set(request.meta["fingerprints"][:-1]).union(
                old_metadata["parents"] if old_metadata else []
            )
        )
        if (
            "cache_expires" in request.meta
            and request.meta["cache_expires"] is not None
        ):
            metadata["cache_expires"] = request.meta["cache_expires"].total_seconds()
        # Write it back.
        rpath = self._get_request_path(spider, request)
        with self._open(os.path.join(rpath, "meta"), "wb") as f:
            f.write(to_bytes(repr(metadata)))
        with self._open(os.path.join(rpath, "pickled_meta"), "wb") as f:
            pickle.dump(metadata, f, protocol=2)

    def _get_request_path(self, spider, request):
        key = request_fingerprint(request, include_headers=["Cookie"])
        return os.path.join(self.cachedir, spider.name, key[0:2], key)

    def item_dropped(self, item, response, exception, spider):
        self.remove_cache_entry(
            self._get_request_path(spider, response.request), remove_parents=True
        )

    def _read_meta_from_path(self, path):
        with open(os.path.join(path, "pickled_meta"), "rb") as f:
            return pickle.load(f)

    def cleanup(self):
        """Removes cache entries in path.

        Entries are removed if one of the conditions is true:
          - Response has a certain status code (e.g. 404).
          - Individual expiration date is reached (compared to now).
          - Timestamp of entry and expires exceeds now.
        """

        logger.debug("Cleaning cache entries from {} ...".format(self.cachedir))

        now = int(datetime.now(timezone.utc).timestamp())
        for cache_entry_path, _dirs, files in os.walk(self.cachedir, topdown=False):
            if "pickled_meta" in files:
                meta = self._read_meta_from_path(cache_entry_path)
                entry_expires_after = min(
                    meta.get("cache_expires", self.expiration_secs),
                    self.expiration_secs
                )
                threshold = meta["timestamp"] + entry_expires_after
                if now > threshold:
                    self.remove_cache_entry(cache_entry_path)
                elif meta["status"] in self.ignore_http_codes:
                    self.remove_cache_entry(cache_entry_path, remove_parents=True)
            elif not os.path.samefile(cache_entry_path, self.cachedir):
                # Try to delete parent directory of cache entries.
                try:
                    os.rmdir(cache_entry_path)
                except OSError:
                    # Not empty, don't care.
                    pass

        logger.debug("Finished cleaning cache entries.")

    def remove_cache_entry(self, cache_entry_path, remove_parents=False):
        try:
            meta = self._read_meta_from_path(cache_entry_path)
        except FileNotFoundError:
            return

        if remove_parents:
            logger.debug(
                "Removing parent cache entries for URL {}".format(meta["response_url"])
            )
            spider_root = os.path.dirname(os.path.dirname(cache_entry_path))
            for fingerprint in meta["parents"]:
                path = os.path.join(spider_root, fingerprint[0:2], fingerprint)
                self.remove_cache_entry(path, remove_parents=False)

        logger.debug("Removing cache entry for URL {}".format(meta["response_url"]))
        shutil.rmtree(cache_entry_path, ignore_errors=True)
