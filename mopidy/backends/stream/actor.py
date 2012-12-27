from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst

import logging
import urlparse

import pykka

from mopidy import settings
from mopidy.backends import base
from mopidy.models import SearchResult, Track

logger = logging.getLogger('mopidy.backends.stream')


class StreamBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, audio):
        super(StreamBackend, self).__init__()

        self.library = StreamLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.playlists = None

        available_protocols = set()

        registry = gst.registry_get_default()
        for factory in registry.get_feature_list(gst.TYPE_ELEMENT_FACTORY):
            for uri in factory.get_uri_protocols():
                if uri in settings.STREAM_PROTOCOLS:
                    available_protocols.add(uri)

        self.uri_schemes = list(available_protocols)


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

    def find_exact(self, **query):
        return SearchResult()

    def search(self, **query):
        return SearchResult()

    def refresh(self, uri=None):
        pass
