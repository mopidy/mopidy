from __future__ import unicode_literals

import logging
import socket

import cherrypy
import ws4py.websocket

from mopidy import core, models
from mopidy.utils import jsonrpc

logger = logging.getLogger(__name__)


class WebSocketResource(object):
    def __init__(self, core_proxy):
        self._core = core_proxy
        inspector = jsonrpc.JsonRpcInspector(
            objects={
                'core.get_uri_schemes': core.Core.get_uri_schemes,
                'core.get_version': core.Core.get_version,
                'core.library': core.LibraryController,
                'core.playback': core.PlaybackController,
                'core.playlists': core.PlaylistsController,
                'core.tracklist': core.TracklistController,
            })
        self.jsonrpc = jsonrpc.JsonRpcWrapper(
            objects={
                'core.describe': inspector.describe,
                'core.get_uri_schemes': self._core.get_uri_schemes,
                'core.get_version': self._core.get_version,
                'core.library': self._core.library,
                'core.playback': self._core.playback,
                'core.playlists': self._core.playlists,
                'core.tracklist': self._core.tracklist,
            },
            decoders=[models.model_json_decoder],
            encoders=[models.ModelJSONEncoder])

    @cherrypy.expose
    def index(self):
        logger.debug('WebSocket handler created')
        cherrypy.request.ws_handler.jsonrpc = self.jsonrpc


class _WebSocket(ws4py.websocket.WebSocket):
    """Sub-class ws4py WebSocket with better error handling."""

    def send(self, *args, **kwargs):
        try:
            super(_WebSocket, self).send(*args, **kwargs)
            return True
        except socket.error as e:
            logger.warning('Send message failed: %s', e)
            # This isn't really correct, but its the only way to break of out
            # the loop in run and trick ws4py into cleaning up.
            self.client_terminated = self.server_terminated = True
            return False

    def close(self, *args, **kwargs):
        try:
            super(_WebSocket, self).close(*args, **kwargs)
        except socket.error as e:
            logger.warning('Closing WebSocket failed: %s', e)


class WebSocketHandler(_WebSocket):
    def opened(self):
        remote = cherrypy.request.remote
        logger.debug(
            'New WebSocket connection from %s:%d',
            remote.ip, remote.port)

    def closed(self, code, reason=None):
        remote = cherrypy.request.remote
        logger.debug(
            'Closed WebSocket connection from %s:%d '
            'with code %s and reason %r',
            remote.ip, remote.port, code, reason)

    def received_message(self, request):
        remote = cherrypy.request.remote
        request = str(request)

        logger.debug(
            'Received WebSocket message from %s:%d: %r',
            remote.ip, remote.port, request)

        response = self.jsonrpc.handle_json(request)
        if response and self.send(response):
            logger.debug(
                'Sent WebSocket message to %s:%d: %r',
                remote.ip, remote.port, response)
