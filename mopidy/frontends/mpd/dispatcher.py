import logging
import re

from pykka import ActorDeadError
from pykka.registry import ActorRegistry

from mopidy import settings
from mopidy.backends.base import Backend
from mopidy.frontends.mpd import exceptions
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

    _noidle = re.compile(r'^noidle$')

    def __init__(self, session=None):
        self.authenticated = False
        self.command_list = False
        self.command_list_ok = False
        self.command_list_index = None
        self.context = MpdContext(self, session=session)

    def handle_request(self, request, current_command_list_index=None):
        """Dispatch incoming requests to the correct handler."""
        self.command_list_index = current_command_list_index
        response = []
        filter_chain = [
            self._catch_mpd_ack_errors_filter,
            self._authenticate_filter,
            self._command_list_filter,
            self._idle_filter,
            self._add_ok_filter,
            self._call_handler_filter,
        ]
        return self._call_next_filter(request, response, filter_chain)

    def handle_idle(self, subsystem):
        self.context.events.add(subsystem)

        subsystems = self.context.subscriptions.intersection(
            self.context.events)
        if not subsystems:
            return

        response = []
        for subsystem in subsystems:
            response.append(u'changed: %s' % subsystem)
        response.append(u'OK')
        self.context.subscriptions = set()
        self.context.events = set()
        self.context.session.send_lines(response)

    def _call_next_filter(self, request, response, filter_chain):
        if filter_chain:
            next_filter = filter_chain.pop(0)
            return next_filter(request, response, filter_chain)
        else:
            return response


    ### Filter: catch MPD ACK errors

    def _catch_mpd_ack_errors_filter(self, request, response, filter_chain):
        try:
            return self._call_next_filter(request, response, filter_chain)
        except exceptions.MpdAckError as mpd_ack_error:
            if self.command_list_index is not None:
                mpd_ack_error.index = self.command_list_index
            return [mpd_ack_error.get_mpd_ack()]


    ### Filter: authenticate

    def _authenticate_filter(self, request, response, filter_chain):
        if self.authenticated:
            return self._call_next_filter(request, response, filter_chain)
        elif settings.MPD_SERVER_PASSWORD is None:
            self.authenticated = True
            return self._call_next_filter(request, response, filter_chain)
        else:
            command_name = request.split(' ')[0]
            command_names_not_requiring_auth = [
                command.name for command in mpd_commands
                if not command.auth_required]
            if command_name in command_names_not_requiring_auth:
                return self._call_next_filter(request, response, filter_chain)
            else:
                raise exceptions.MpdPermissionError(command=command_name)


    ### Filter: command list

    def _command_list_filter(self, request, response, filter_chain):
        if self._is_receiving_command_list(request):
            self.command_list.append(request)
            return []
        else:
            response = self._call_next_filter(request, response, filter_chain)
            if (self._is_receiving_command_list(request) or
                    self._is_processing_command_list(request)):
                if response and response[-1] == u'OK':
                    response = response[:-1]
            return response

    def _is_receiving_command_list(self, request):
        return (self.command_list is not False
            and request != u'command_list_end')

    def _is_processing_command_list(self, request):
        return (self.command_list_index is not None
            and request != u'command_list_end')


    ### Filter: idle

    def _idle_filter(self, request, response, filter_chain):
        if self._is_currently_idle() and not self._noidle.match(request):
            logger.debug(u'Client sent us %s, only %s is allowed while in '
                'the idle state', repr(request), repr(u'noidle'))
            self.context.session.close()
            return []

        if not self._is_currently_idle() and self._noidle.match(request):
            return [] # noidle was called before idle

        response = self._call_next_filter(request, response, filter_chain)

        if self._is_currently_idle():
            return []
        else:
            return response

    def _is_currently_idle(self):
        return bool(self.context.subscriptions)


    ### Filter: add OK

    def _add_ok_filter(self, request, response, filter_chain):
        response = self._call_next_filter(request, response, filter_chain)
        if not self._has_error(response):
            response.append(u'OK')
        return response

    def _has_error(self, response):
        return response and response[-1].startswith(u'ACK')


    ### Filter: call handler

    def _call_handler_filter(self, request, response, filter_chain):
        try:
            response = self._format_response(self._call_handler(request))
            return self._call_next_filter(request, response, filter_chain)
        except ActorDeadError as e:
            logger.warning(u'Tried to communicate with dead actor.')
            raise exceptions.MpdSystemError(e)

    def _call_handler(self, request):
        (handler, kwargs) = self._find_handler(request)
        return handler(self.context, **kwargs)

    def _find_handler(self, request):
        for pattern in request_handlers:
            matches = re.match(pattern, request)
            if matches is not None:
                return (request_handlers[pattern], matches.groupdict())
        command_name = request.split(' ')[0]
        if command_name in [command.name for command in mpd_commands]:
            raise exceptions.MpdArgError(u'incorrect arguments',
                command=command_name)
        raise exceptions.MpdUnknownCommand(command=command_name)

    def _format_response(self, response):
        formatted_response = []
        for element in self._listify_result(response):
            formatted_response.extend(self._format_lines(element))
        return formatted_response

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


class MpdContext(object):
    """
    This object is passed as the first argument to all MPD command handlers to
    give the command handlers access to important parts of Mopidy.
    """

    #: The current :class:`MpdDispatcher`.
    dispatcher = None

    #: The current :class:`mopidy.frontends.mpd.MpdSession`.
    session = None

    #: The active subsystems that have pending events.
    events = None

    #: The subsytems that we want to be notified about in idle mode.
    subscriptions = None

    def __init__(self, dispatcher, session=None):
        self.dispatcher = dispatcher
        self.session = session
        self.events = set()
        self.subscriptions = set()
        self._backend = None
        self._mixer = None

    @property
    def backend(self):
        """
        The backend. An instance of :class:`mopidy.backends.base.Backend`.
        """
        if self._backend is None:
            backend_refs = ActorRegistry.get_by_class(Backend)
            assert len(backend_refs) == 1, \
                'Expected exactly one running backend.'
            self._backend = backend_refs[0].proxy()
        return self._backend

    @property
    def mixer(self):
        """
        The mixer. An instance of :class:`mopidy.mixers.base.BaseMixer`.
        """
        if self._mixer is None:
            mixer_refs = ActorRegistry.get_by_class(BaseMixer)
            assert len(mixer_refs) == 1, 'Expected exactly one running mixer.'
            self._mixer = mixer_refs[0].proxy()
        return self._mixer
