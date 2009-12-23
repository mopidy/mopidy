import logging
import re

from mopidy import settings

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
    def handle_request(self, request):
        for pattern in _request_handlers:
            matches = re.match(pattern, request)
            if matches is not None:
                groups = matches.groupdict()
                return _request_handlers[pattern](self, **groups)
        logger.warning(u'Unhandled request: %s', request)

    @register(r'^currentsong$')
    def _currentsong(self):
        return None # TODO

    @register(r'^listplaylists$')
    def _listplaylists(self):
        return None # TODO

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
        return None # TODO

    @register(r'^status$')
    def _status(self):
        # TODO
        return [
            'volume: 0',
            'repeat: 0',
            'random: 0',
            'single: 0',
            'consume: 0',
            'playlist: 0',
            'playlistlength: 0',
            'xfade: 0',
            'state: stop',
        ]
