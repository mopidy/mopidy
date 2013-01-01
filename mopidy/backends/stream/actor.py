from __future__ import unicode_literals

import logging
import urlparse

import pykka

from mopidy import settings
from mopidy.audio import utils
from mopidy.backends import base
from mopidy.models import SearchResult, Track

logger = logging.getLogger('mopidy.backends.stream')


class StreamBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, audio):
        super(StreamBackend, self).__init__()

        self.library = StreamLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.playlists = None

        self.uri_schemes = utils.supported_uri_schemes(
            settings.STREAM_PROTOCOLS)


# TODO: Should we consider letting lookup know how to expand common playlist
# formats (m3u, pls, etc) for http(s) URIs?
class StreamLibraryProvider(base.BaseLibraryProvider):
    def lookup(self, uri):
        if urlparse.urlsplit(uri).scheme not in self.backend.uri_schemes:
            return []
        # TODO: actually lookup the stream metadata by getting tags in same
        # way as we do for updating the local library with mopidy.scanner
        # Note that we would only want the stream metadata at this stage,
        # not the currently playing track's.
        return [Track(uri=uri, name=uri)]
