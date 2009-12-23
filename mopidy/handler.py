import logging
import re

from mopidy import settings
from mopidy.backends.dummy_backend import DummyBackend

logger = logging.getLogger('handler')

global _request_handlers
_request_handlers = {}

def register(pattern):
    def decorator(func):
        global _request_handlers
        if pattern in _request_handlers:
            raise ValueError(u'Tried to redefine handler for %s with %s' % (
                pattern, func))
        _request_handlers[pattern] = func
        return func
    return decorator

class MpdHandler(object):
    def __init__(self, backend=DummyBackend):
        self.register_backend(backend())

    def handle_request(self, request):
        for pattern in _request_handlers:
            matches = re.match(pattern, request)
            if matches is not None:
                groups = matches.groupdict()
                return _request_handlers[pattern](self, **groups)
        logger.warning(u'Unhandled request: %s', request)

    def register_backend(self, backend):
        self.backend = backend

    @register(r'^currentsong$')
    def _currentsong(self):
        return self.backend.current_song()

    @register(r'^listplaylists$')
    def _listplaylists(self):
        return self.backend.list_playlists()

    @register(r'^lsinfo( "(?P<uri>[^"]*)")*$')
    def _lsinfo(self, uri):
        if uri == u'/':
            return self._listplaylists()
        return None # TODO

    @register(r'^ping$')
    def _ping(self):
        return None

    @register(r'^plchanges "(?P<version>\d+)"$')
    def _plchanges(self, version):
        return self.backend.playlist_changes(version)

    @register(r'^status$')
    def _status(self):
        return {
            'volume': self.backend.status_volume(),
            'repeat': self.backend.status_repeat(),
            'random': self.backend.status_random(),
            'single': self.backend.status_single(),
            'consume': self.backend.status_consume(),
            'playlist': self.backend.status_playlist(),
            'playlistlength': self.backend.status_playlist_length(),
            'xfade': self.backend.status_xfade(),
            'state': self.backend.status_state(),
        }
