from __future__ import absolute_import, unicode_literals

import fnmatch
import logging
import re
import time
import urlparse

import pykka

import requests

from mopidy import audio as audio_lib, backend, exceptions, stream
from mopidy.audio import scan, utils
from mopidy.internal import http, playlists
from mopidy.models import Track

logger = logging.getLogger(__name__)


class StreamBackend(pykka.ThreadingActor, backend.Backend):

    def __init__(self, config, audio):
        super(StreamBackend, self).__init__()

        self._scanner = scan.Scanner(
            timeout=config['stream']['timeout'],
            proxy_config=config['proxy'])

        self.library = StreamLibraryProvider(
            backend=self, blacklist=config['stream']['metadata_blacklist'])
        self.playback = StreamPlaybackProvider(
            audio=audio, backend=self, config=config)
        self.playlists = None

        self.uri_schemes = audio_lib.supported_uri_schemes(
            config['stream']['protocols'])


class StreamLibraryProvider(backend.LibraryProvider):

    def __init__(self, backend, blacklist):
        super(StreamLibraryProvider, self).__init__(backend)
        self._scanner = backend._scanner
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
            track = utils.convert_tags_to_track(result.tags).replace(
                uri=uri, length=result.duration)
        except exceptions.ScannerError as e:
            logger.warning('Problem looking up %s: %s', uri, e)
            track = Track(uri=uri)

        return [track]


class StreamPlaybackProvider(backend.PlaybackProvider):

    def __init__(self, audio, backend, config):
        super(StreamPlaybackProvider, self).__init__(audio, backend)
        self._config = config
        self._scanner = backend._scanner

    def translate_uri(self, uri):
        try:
            scan_result = self._scanner.scan(uri)
        except exceptions.ScannerError as e:
            logger.warning(
                'Problem scanning URI %s: %s', uri, e)
            return None

        if not (scan_result.mime.startswith('text/') or
                scan_result.mime.startswith('application/')):
            return uri

        content = self._download(uri)
        if content is None:
            return None

        tracks = list(playlists.parse(content))
        if tracks:
            # TODO Test streams and return first that seems to be playable
            return tracks[0]

    def _download(self, uri):
        timeout = self._config['stream']['timeout'] / 1000.0

        session = http.get_requests_session(
            proxy_config=self._config['proxy'],
            user_agent='%s/%s' % (
                stream.Extension.dist_name, stream.Extension.version))

        try:
            response = session.get(
                uri, stream=True, timeout=timeout)
        except requests.exceptions.Timeout:
            logger.warning(
                'Download of stream playlist (%s) failed due to connection '
                'timeout after %.3fs', uri, timeout)
            return None

        deadline = time.time() + timeout
        content = []
        for chunk in response.iter_content(4096):
            content.append(chunk)
            if time.time() > deadline:
                logger.warning(
                    'Download of stream playlist (%s) failed due to download '
                    'taking more than %.3fs', uri, timeout)
                return None

        if not response.ok:
            logger.warning(
                'Problem downloading stream playlist %s: %s',
                uri, response.reason)
            return None

        return b''.join(content)
