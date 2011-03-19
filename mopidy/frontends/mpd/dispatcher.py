import re

from pykka.registry import ActorRegistry

from mopidy.backends.base import Backend
from mopidy.frontends.mpd.exceptions import (MpdAckError, MpdArgError,
    MpdUnknownCommand)
from mopidy.frontends.mpd.protocol import mpd_commands, request_handlers
# Do not remove the following import. The protocol modules must be imported to
# get them registered as request handlers.
# pylint: disable = W0611
from mopidy.frontends.mpd.protocol import (audio_output, command_list,
    connection, current_playlist, empty, music_db, playback, reflection,
    status, stickers, stored_playlists)
# pylint: enable = W0611
from mopidy.mixers.base import BaseMixer
from mopidy.utils import flatten

class MpdDispatcher(object):
    """
    The MPD session feeds the MPD dispatcher with requests. The dispatcher
    finds the correct handler, processes the request and sends the response
    back to the MPD session.
    """

    # XXX Consider merging MpdDispatcher into MpdSession

    def __init__(self):
        backend_refs = ActorRegistry.get_by_class(Backend)
        assert len(backend_refs) == 1, 'Expected exactly one running backend.'
        self.backend = backend_refs[0].proxy()

        mixer_refs = ActorRegistry.get_by_class(BaseMixer)
        assert len(mixer_refs) == 1, 'Expected exactly one running mixer.'
        self.mixer = mixer_refs[0].proxy()

        self.command_list = False
        self.command_list_ok = False

    def handle_request(self, request, command_list_index=None):
        """Dispatch incoming requests to the correct handler."""
        if self.command_list is not False and request != u'command_list_end':
            self.command_list.append(request)
            return None
        try:
            (handler, kwargs) = self.find_handler(request)
            result = handler(self, **kwargs)
        except MpdAckError as e:
            if command_list_index is not None:
                e.index = command_list_index
            return self.handle_response(e.get_mpd_ack(), add_ok=False)
        if request in (u'command_list_begin', u'command_list_ok_begin'):
            return None
        if command_list_index is not None:
            return self.handle_response(result, add_ok=False)
        return self.handle_response(result)

    def find_handler(self, request):
        """Find the correct handler for a request."""
        for pattern in request_handlers:
            matches = re.match(pattern, request)
            if matches is not None:
                return (request_handlers[pattern], matches.groupdict())
        command = request.split(' ')[0]
        if command in mpd_commands:
            raise MpdArgError(u'incorrect arguments', command=command)
        raise MpdUnknownCommand(command=command)

    def handle_response(self, result, add_ok=True):
        """Format the response from a request handler."""
        response = []
        if result is None:
            result = []
        elif isinstance(result, set):
            result = list(result)
        elif not isinstance(result, list):
            result = [result]
        for line in flatten(result):
            if isinstance(line, dict):
                for (key, value) in line.items():
                    response.append(u'%s: %s' % (key, value))
            elif isinstance(line, tuple):
                (key, value) = line
                response.append(u'%s: %s' % (key, value))
            else:
                response.append(line)
        if add_ok and (not response or not response[-1].startswith(u'ACK')):
            response.append(u'OK')
        return response
