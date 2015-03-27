from __future__ import absolute_import, unicode_literals

import fnmatch
import logging
import re
import urlparse

import pykka

from mopidy import audio as audio_lib, backend, exceptions
from mopidy.audio import scan, utils
from mopidy.models import Track

logger = logging.getLogger(__name__)


class StreamBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(StreamBackend, self).__init__()

        self.library = StreamLibraryProvider(
            backend=self, timeout=config['stream']['timeout'],
            blacklist=config['stream']['metadata_blacklist'],
            proxy=config['proxy'])
        self.playback = backend.PlaybackProvider(audio=audio, backend=self)
        self.playlists = None

        self.uri_schemes = audio_lib.supported_uri_schemes(
            config['stream']['protocols'])


class StreamLibraryProvider(backend.LibraryProvider):
    def __init__(self, backend, timeout, blacklist, proxy):
        super(StreamLibraryProvider, self).__init__(backend)
        self._scanner = scan.Scanner(timeout=timeout, proxy_config=proxy)
        self._blacklist_re = re.compile(
            r'^(%s)$' % '|'.join(fnmatch.translate(u) for u in blacklist))

    def lookup(self, uri):
        if urlparse.urlsplit(uri).scheme not in self.backend.uri_schemes:
            return []

        if self._blacklist_re.match(uri):
            logger.debug('URI matched metadata lookup blacklist: %s', uri)
            return [Track(uri=uri)]

        try:
            result = self._scanner.scan(uri)
            track = utils.convert_tags_to_track(result.tags).copy(
                uri=uri, length=result.duration)
        except exceptions.ScannerError as e:
            logger.warning('Problem looking up %s: %s', uri, e)
            track = Track(uri=uri)

        return [track]
