import logging
import re

from pykka import ActorDeadError
from pykka.registry import ActorRegistry

from mopidy import settings
from mopidy.backends.base import Backend
from mopidy.frontends.mpd.exceptions import (MpdAckError, MpdArgError,
    MpdUnknownCommand, MpdSystemError)
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

logger = logging.getLogger('mopidy.frontends.mpd.dispatcher')

class MpdDispatcher(object):
    """
    The MPD session feeds the MPD dispatcher with requests. The dispatcher
    finds the correct handler, processes the request and sends the response
    back to the MPD session.
    """

    def __init__(self, session=None):
        self.authenticated = False
        self.command_list = False
        self.command_list_ok = False
        self.context = MpdContext(self, session=session)

    def handle_request(self, request, current_command_list_index=None):
        """Dispatch incoming requests to the correct handler."""
        if not self.authenticated:
            (self.authenticated, result) = self._check_password(request)
            if result:
                return result

        if self._is_receiving_command_list(request):
            self.command_list.append(request)
            return None

        try:
            try:
                result = self._call_handler(request)
            except ActorDeadError as e:
                logger.warning(u'Tried to communicate with dead actor.')
                raise MpdSystemError(e.message)
        except MpdAckError as e:
            if current_command_list_index is not None:
                e.index = current_command_list_index
            return self._format_response(e.get_mpd_ack(), add_ok=False)

        if (request in (u'command_list_begin', u'command_list_ok_begin')
                or current_command_list_index is not None):
            return self._format_response(result, add_ok=False)

        return self._format_response(result)

    def _check_password(self, request):
        """
        Takes any request and tries to authenticate the client using it.

        :rtype: a two-tuple containing (is_authenticated, response_message). If
            the response_message is :class:`None`, normal processing should
            continue, even though the client may not be authenticated.
        """
        if settings.MPD_SERVER_PASSWORD is None:
            return (True, None)
        command = request.split(' ')[0]
        if command == 'password':
            if request == 'password "%s"' % settings.MPD_SERVER_PASSWORD:
                return (True, [u'OK'])
            else:
                return (False, [u'ACK [3@0] {password} incorrect password'])
        if command in ('close', 'commands', 'notcommands', 'ping'):
            return (False, None)
        else:
            return (False,
                [u'ACK [4@0] {%(c)s} you don\'t have permission for "%(c)s"' %
                {'c': command}])

    def _is_receiving_command_list(self, request):
        return (self.command_list is not False
            and request != u'command_list_end')

    def _call_handler(self, request):
        (handler, kwargs) = self._find_handler(request)
        return handler(self.context, **kwargs)

    def _find_handler(self, request):
        for pattern in request_handlers:
            matches = re.match(pattern, request)
            if matches is not None:
                return (request_handlers[pattern], matches.groupdict())
        command = request.split(' ')[0]
        if command in mpd_commands:
            raise MpdArgError(u'incorrect arguments', command=command)
        raise MpdUnknownCommand(command=command)

    def _format_response(self, result, add_ok=True):
        response = []
        for element in self._listify_result(result):
            response.extend(self._format_lines(element))
        if add_ok and (not response or not self._has_error(response)):
            response.append(u'OK')
        return response

    def _listify_result(self, result):
        if result is None:
            return []
        if isinstance(result, set):
            return flatten(list(result))
        if not isinstance(result, list):
            return [result]
        return flatten(result)

    def _format_lines(self, line):
        if isinstance(line, dict):
            return [u'%s: %s' % (key, value) for (key, value) in line.items()]
        if isinstance(line, tuple):
            (key, value) = line
            return [u'%s: %s' % (key, value)]
        return [line]

    def _has_error(self, response):
        return bool(response) and response[-1].startswith(u'ACK')


class MpdContext(object):
    """
    This object is passed as the first argument to all MPD command handlers to
    give the command handlers access to important parts of Mopidy.
    """

    #: The current :class:`MpdDispatcher`.
    dispatcher = None

    #: The current :class:`mopidy.frontends.mpd.session.MpdSession`.
    session = None

    def __init__(self, dispatcher, session=None):
        self.dispatcher = dispatcher
        self.session = session
        self._backend = None
        self._mixer = None

    @property
    def backend(self):
        """
        The backend. An instance of :class:`mopidy.backends.base.Backend`.
        """
        if self._backend is not None:
            return self._backend
        backend_refs = ActorRegistry.get_by_class(Backend)
        assert len(backend_refs) == 1, 'Expected exactly one running backend.'
        self._backend = backend_refs[0].proxy()
        return self._backend

    @property
    def mixer(self):
        """
        The mixer. An instance of :class:`mopidy.mixers.base.BaseMixer`.
        """
        if self._mixer is not None:
            return self._mixer
        mixer_refs = ActorRegistry.get_by_class(BaseMixer)
        assert len(mixer_refs) == 1, 'Expected exactly one running mixer.'
        self._mixer = mixer_refs[0].proxy()
        return self._mixer
