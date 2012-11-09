from __future__ import absolute_import

import logging

import pykka

from mopidy import exceptions, settings
from mopidy.core import CoreListener

try:
    import cherrypy
    from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
    from ws4py.websocket import WebSocket
    from ws4py.messaging import TextMessage
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)


logger = logging.getLogger('mopidy.frontends.http')


class HttpFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, core):
        super(HttpFrontend, self).__init__()
        self.core = core
        self._setup_server()
        self._setup_websocket_plugin()
        app = self._create_app()
        self._setup_logging(app)

    def _setup_server(self):
        cherrypy.config.update({
            'engine.autoreload_on': False,
            'server.socket_host':
                settings.HTTP_SERVER_HOSTNAME.encode('utf-8'),
            'server.socket_port': settings.HTTP_SERVER_PORT,
        })

    def _setup_websocket_plugin(self):
        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()

    def _create_app(self):
        return cherrypy.tree.mount(Root(self.core), '/', {
            '/ws': {
                'tools.websocket.on': True,
                'tools.websocket.handler_cls': EventWebSocketHandler,
            },
        })

    def _setup_logging(self, app):
        cherrypy.log.access_log.setLevel(logging.NOTSET)
        cherrypy.log.error_log.setLevel(logging.NOTSET)
        cherrypy.log.screen = False

        app.log.access_log.setLevel(logging.NOTSET)
        app.log.error_log.setLevel(logging.NOTSET)

    def on_start(self):
        logger.debug(u'Starting HTTP server')
        cherrypy.engine.start()
        logger.info(u'HTTP server running at %s', cherrypy.server.base())

    def on_stop(self):
        logger.debug(u'Stopping HTTP server')
        cherrypy.engine.stop()
        logger.info(u'Stopped HTTP server')

    def playback_state_changed(self, old_state, new_state):
        cherrypy.engine.publish('websocket-broadcast',
            TextMessage('playback_state_changed: %s -> %s' % (
                old_state, new_state)))


class EventWebSocketHandler(WebSocket):
    def opened(self):
        remote = cherrypy.request.remote
        logger.debug(u'New WebSocket connection from %s:%d',
            remote.ip, remote.port)

    def closed(self, code, reason=None):
        remote = cherrypy.request.remote
        logger.debug(u'Closed WebSocket connection from %s:%d '
            'with code %s and reason %r',
            remote.ip, remote.port, code, reason)

    def received_message(self, message):
        remote = cherrypy.request.remote
        logger.debug(u'Received WebSocket message from %s:%d: %s',
            remote.ip, remote.port, message)
        # This is where we would handle incoming messages from the clients


class Root(object):
    def __init__(self, core):
        self.core = core

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        playback_state = self.core.playback.state.get()
        track = self.core.playback.current_track.get()
        if track:
            track = track.serialize()
        return {
            'playback_state': playback_state,
            'current_track': track,
        }

    @cherrypy.expose
    def ws(self):
        logger.debug(u'WebSocket handler created')
