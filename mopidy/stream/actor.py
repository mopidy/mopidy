from __future__ import absolute_import, unicode_literals

import fnmatch
import logging
import re
import time

import pykka

from mopidy import audio as audio_lib, backend, exceptions, stream
from mopidy.audio import scan, tags
from mopidy.compat import urllib
from mopidy.internal import http, playlists
from mopidy.models import Track

logger = logging.getLogger(__name__)


class StreamBackend(pykka.ThreadingActor, backend.Backend):

    def __init__(self, config, audio):
        super(StreamBackend, self).__init__()

        self._scanner = scan.Scanner(
            timeout=config['stream']['timeout'],
            proxy_config=config['proxy'])

        self._session = http.get_requests_session(
            proxy_config=config['proxy'],
            user_agent='%s/%s' % (
                stream.Extension.dist_name, stream.Extension.version))

        blacklist = config['stream']['metadata_blacklist']
        self._blacklist_re = re.compile(
            r'^(%s)$' % '|'.join(fnmatch.translate(u) for u in blacklist))

        self._timeout = config['stream']['timeout']

        self.library = StreamLibraryProvider(backend=self)
        self.playback = StreamPlaybackProvider(audio=audio, backend=self)
        self.playlists = None

        self.uri_schemes = audio_lib.supported_uri_schemes(
            config['stream']['protocols'])

        if 'file' in self.uri_schemes and config['file']['enabled']:
            logger.warning(
                'The stream/protocols config value includes the "file" '
                'protocol. "file" playback is now handled by Mopidy-File. '
                'Please remove it from the stream/protocols config.')
            self.uri_schemes -= {'file'}


class StreamLibraryProvider(backend.LibraryProvider):
    def lookup(self, uri):
        if urllib.parse.urlsplit(uri).scheme not in self.backend.uri_schemes:
            return []

        if self.backend._blacklist_re.match(uri):
            logger.debug('URI matched metadata lookup blacklist: %s', uri)
            return [Track(uri=uri)]

        _, scan_result = _unwrap_stream(
            uri, timeout=self.backend._timeout, scanner=self.backend._scanner,
            requests_session=self.backend._session)

        if scan_result:
            track = tags.convert_tags_to_track(scan_result.tags).replace(
                uri=uri, length=scan_result.duration)
        else:
            logger.warning('Problem looking up %s', uri)
            track = Track(uri=uri)

        return [track]


class StreamPlaybackProvider(backend.PlaybackProvider):

    def translate_uri(self, uri):
        if urllib.parse.urlsplit(uri).scheme not in self.backend.uri_schemes:
            return None

        if self.backend._blacklist_re.match(uri):
            logger.debug('URI matched metadata lookup blacklist: %s', uri)
            return uri

        unwrapped_uri, _ = _unwrap_stream(
            uri, timeout=self.backend._timeout, scanner=self.backend._scanner,
            requests_session=self.backend._session)
        return unwrapped_uri


# TODO: cleanup the return value of this.
def _unwrap_stream(uri, timeout, scanner, requests_session):
    """
    Get a stream URI from a playlist URI, ``uri``.

    Unwraps nested playlists until something that's not a playlist is found or
    the ``timeout`` is reached.
    """

    original_uri = uri
    seen_uris = set()
    deadline = time.time() + timeout

    while time.time() < deadline:
        if uri in seen_uris:
            logger.info(
                'Unwrapping stream from URI (%s) failed: '
                'playlist referenced itself', uri)
            return None, None
        else:
            seen_uris.add(uri)

        logger.debug('Unwrapping stream from URI: %s', uri)

        try:
            scan_timeout = deadline - time.time()
            if scan_timeout < 0:
                logger.info(
                    'Unwrapping stream from URI (%s) failed: '
                    'timed out in %sms', uri, timeout)
                return None, None
            scan_result = scanner.scan(uri, timeout=scan_timeout)
        except exceptions.ScannerError as exc:
            logger.debug('GStreamer failed scanning URI (%s): %s', uri, exc)
            scan_result = None

        if scan_result is not None:
            if scan_result.playable or (
                not scan_result.mime.startswith('text/') and
                not scan_result.mime.startswith('application/')
            ):
                logger.debug(
                    'Unwrapped potential %s stream: %s', scan_result.mime, uri)
                return uri, scan_result

        download_timeout = deadline - time.time()
        if download_timeout < 0:
            logger.info(
                'Unwrapping stream from URI (%s) failed: timed out in %sms',
                uri, timeout)
            return None, None
        content = http.download(
            requests_session, uri, timeout=download_timeout / 1000)

        if content is None:
            logger.info(
                'Unwrapping stream from URI (%s) failed: '
                'error downloading URI %s', original_uri, uri)
            return None, None

        uris = playlists.parse(content)
        if not uris:
            logger.debug(
                'Failed parsing URI (%s) as playlist; found potential stream.',
                uri)
            return uri, None

        # TODO Test streams and return first that seems to be playable
        logger.debug(
            'Parsed playlist (%s) and found new URI: %s', uri, uris[0])
        uri = uris[0]
