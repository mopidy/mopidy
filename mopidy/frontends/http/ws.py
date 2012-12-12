from __future__ import unicode_literals

import logging

from mopidy import core, exceptions, models
from mopidy.utils import jsonrpc

try:
    import cherrypy
    from ws4py.websocket import WebSocket
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)


logger = logging.getLogger('mopidy.frontends.http')


class WebSocketResource(object):
    def __init__(self, core_proxy):
        self._core = core_proxy
        inspector = jsonrpc.JsonRpcInspector(
            objects={
                'core.library': core.LibraryController,
                'core.playback': core.PlaybackController,
                'core.playlists': core.PlaylistsController,
                'core.tracklist': core.TracklistController,
            })
        self.jsonrpc = jsonrpc.JsonRpcWrapper(
            objects={
                'core.describe': inspector.describe,
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


class WebSocketHandler(WebSocket):
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
        if response:
            self.send(response)
            logger.debug(
                'Sent WebSocket message to %s:%d: %r',
                remote.ip, remote.port, response)
