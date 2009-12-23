import logging
import re

from mopidy import settings

logger = logging.getLogger('handler')

class MpdHandler(object):
    def __init__(self):
        self.request_handlers = [
            (r'^currentsong$', self._currentsong),
            (r'^listplaylists$', self._listplaylists),
            (r'^lsinfo( "(?P<uri>[^"]*)")*$', self._lsinfo),
            (r'^ping$', self._ping),
            (r'^plchanges "(?P<version>\d+)"$', self._plchanges),
            (r'^status$', self._status),
        ]

    def handle_request(self, request):
        for request_pattern, request_handling_method in self.request_handlers:
            matches = re.match(request_pattern, request)
            if matches is not None:
                groups = matches.groupdict()
                return request_handling_method(**groups)
        logger.warning(u'Unhandled request: %s', request)

    def _currentsong(self):
        return None # TODO

    def _listplaylists(self):
        return None # TODO

    def _lsinfo(self, uri):
        if uri == u'/':
            return self._listplaylists()
        return None # TODO

    def _ping(self):
        return None

    def _plchanges(self, version):
        return None # TODO

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
