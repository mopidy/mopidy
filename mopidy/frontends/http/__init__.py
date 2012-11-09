from __future__ import absolute_import

import logging

import pykka

from mopidy import exceptions, settings

try:
    import cherrypy
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)


logger = logging.getLogger('mopidy.frontends.http')


class HttpFrontend(pykka.ThreadingActor):
    def __init__(self, core):
        super(HttpFrontend, self).__init__()
        self.core = core
        cherrypy.config.update({
            'engine.autoreload_on': False,
            'server.socket_host':
                settings.HTTP_SERVER_HOSTNAME.encode('utf-8'),
            'server.socket_port': settings.HTTP_SERVER_PORT,
        })
        app = cherrypy.tree.mount(Root(self.core), '/')
        self._setup_logging(app)

    def _setup_logging(self, app):
        cherrypy.log.access_log.setLevel(logging.NOTSET)
        cherrypy.log.error_log.setLevel(logging.NOTSET)
        cherrypy.log.screen = False

        app.log.access_log.setLevel(logging.NOTSET)
        app.log.error_log.setLevel(logging.NOTSET)

    def on_start(self):
        logger.debug(u'Starting HTTP server')
        cherrypy.engine.start()
        logger.info(u'HTTP server running at %s',
            cherrypy.server.base())

    def on_stop(self):
        cherrypy.engine.stop()


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
