from __future__ import absolute_import

import logging

import cherrypy
import pykka


logger = logging.getLogger('mopidy.frontends.cherrypyhttp')


class CherryPyHttpFrontend(pykka.ThreadingActor):
    def __init__(self, core):
        super(CherryPyHttpFrontend, self).__init__()
        self.core = core

    def on_start(self):
        logger.debug(u'Starting CherryPy HTTP server')
        cherrypy.tree.mount(Root(self.core), '/', {})
        cherrypy.server.socket_port = 6680
        cherrypy.server.start()
        logger.info(u'CherryPy HTTP server running at %s',
            cherrypy.server.base())

    def on_stop(self):
        cherrypy.server.stop()


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
