from __future__ import unicode_literals

import logging

from mopidy import exceptions

try:
    import cherrypy
    from ws4py.websocket import WebSocket
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)


logger = logging.getLogger('mopidy.frontends.http')


class WebSocketResource(object):
    @cherrypy.expose
    def index(self):
        logger.debug('WebSocket handler created')


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

    def received_message(self, message):
        remote = cherrypy.request.remote
        logger.debug(
            'Received WebSocket message from %s:%d: %s',
            remote.ip, remote.port, message)
        # This is where we would handle incoming messages from the clients
