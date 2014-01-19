from __future__ import unicode_literals

import logging
import urlparse

import pykka

from mopidy import audio as audio_lib, backend, exceptions
from mopidy.audio import scan
from mopidy.models import Track

logger = logging.getLogger(__name__)


class StreamBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(StreamBackend, self).__init__()

        self.library = StreamLibraryProvider(
            backend=self, timeout=config['stream']['timeout'])
        self.playback = backend.PlaybackProvider(audio=audio, backend=self)
        self.playlists = None

        self.uri_schemes = audio_lib.supported_uri_schemes(
            config['stream']['protocols'])


class StreamLibraryProvider(backend.LibraryProvider):
    def __init__(self, backend, timeout):
        super(StreamLibraryProvider, self).__init__(backend)
        self._scanner = scan.Scanner(min_duration=None, timeout=timeout)

    def lookup(self, uri):
        if urlparse.urlsplit(uri).scheme not in self.backend.uri_schemes:
            return []

        try:
            data = self._scanner.scan(uri)
            track = scan.audio_data_to_track(data)
        except exceptions.ScannerError as e:
            logger.warning('Problem looking up %s: %s', uri, e)
            track = Track(uri=uri, name=uri)

        return [track]
