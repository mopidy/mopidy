from __future__ import unicode_literals

import logging
import json
import os

import pykka

from mopidy import exceptions, models, settings
from mopidy.core import CoreListener

try:
    import cherrypy
    from ws4py.messaging import TextMessage
    from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)

from . import api, ws


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
            'server.socket_host': (
                settings.HTTP_SERVER_HOSTNAME.encode('utf-8')),
            'server.socket_port': settings.HTTP_SERVER_PORT,
        })

    def _setup_websocket_plugin(self):
        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()

    def _create_app(self):
        root = RootResource()
        root.api = api.ApiResource(self.core)
        root.ws = ws.WebSocketResource(self.core)

        if settings.HTTP_SERVER_STATIC_DIR:
            static_dir = settings.HTTP_SERVER_STATIC_DIR
        else:
            static_dir = os.path.join(os.path.dirname(__file__), 'data')
        logger.debug('HTTP server will serve "%s" at /', static_dir)

        config = {
            b'/': {
                'tools.staticdir.on': True,
                'tools.staticdir.index': 'index.html',
                'tools.staticdir.dir': static_dir,
            },
            b'/api': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            },
            b'/ws': {
                'tools.websocket.on': True,
                'tools.websocket.handler_cls': ws.WebSocketHandler,
            },
        }

        return cherrypy.tree.mount(root, '/', config)

    def _setup_logging(self, app):
        cherrypy.log.access_log.setLevel(logging.NOTSET)
        cherrypy.log.error_log.setLevel(logging.NOTSET)
        cherrypy.log.screen = False

        app.log.access_log.setLevel(logging.NOTSET)
        app.log.error_log.setLevel(logging.NOTSET)

    def on_start(self):
        logger.debug('Starting HTTP server')
        cherrypy.engine.start()
        logger.info('HTTP server running at %s', cherrypy.server.base())

    def on_stop(self):
        logger.debug('Stopping HTTP server')
        cherrypy.engine.exit()
        logger.info('Stopped HTTP server')

    def track_playback_paused(self, **data):
        self._broadcast_event('track_playback_paused', data)

    def track_playback_resumed(self, **data):
        self._broadcast_event('track_playback_resumed', data)

    def track_playback_started(self, **data):
        self._broadcast_event('track_playback_started', data)

    def track_playback_ended(self, **data):
        self._broadcast_event('track_playback_ended', data)

    def playback_state_changed(self, **data):
        self._broadcast_event('playback_state_changed', data)

    def tracklist_changed(self, **data):
        self._broadcast_event('tracklist_changed', data)

    def playlists_loaded(self, **data):
        self._broadcast_event('playlists_loaded', data)

    def playlist_changed(self, **data):
        self._broadcast_event('playlist_changed', data)

    def options_changed(self, **data):
        self._broadcast_event('options_changed', data)

    def volume_changed(self, **data):
        self._broadcast_event('volume_changed', data)

    def seeked(self, **data):
        self._broadcast_event('seeked', data)

    def _broadcast_event(self, name, data):
        event = {}
        event.update(data)
        event['event'] = name
        message = json.dumps(event, cls=models.ModelJSONEncoder)
        cherrypy.engine.publish('websocket-broadcast', TextMessage(message))


class RootResource(object):
    pass
