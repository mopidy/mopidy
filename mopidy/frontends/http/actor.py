from __future__ import unicode_literals

import logging
import json
import os

import cherrypy
import pykka
from ws4py.messaging import TextMessage
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool

from mopidy import models
from mopidy.core import CoreListener
from mopidy.utils import zeroconf
from . import ws


logger = logging.getLogger('mopidy.frontends.http')


class HttpFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super(HttpFrontend, self).__init__()
        self.config = config
        self.core = core

        self.hostname = config['http']['hostname']
        self.port = config['http']['port']
        self.zeroconf_name = config['http']['zeroconf']
        self.zeroconf_service = None

        self._setup_server()
        self._setup_websocket_plugin()
        app = self._create_app()
        self._setup_logging(app)

    def _setup_server(self):
        cherrypy.config.update({
            'engine.autoreload_on': False,
            'server.socket_host': self.hostname,
            'server.socket_port': self.port,
        })

    def _setup_websocket_plugin(self):
        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()

    def _create_app(self):
        root = RootResource()
        root.mopidy = MopidyResource()
        root.mopidy.ws = ws.WebSocketResource(self.core)

        if self.config['http']['static_dir']:
            static_dir = self.config['http']['static_dir']
        else:
            static_dir = os.path.join(os.path.dirname(__file__), 'data')
        logger.debug('HTTP server will serve "%s" at /', static_dir)

        mopidy_dir = os.path.join(os.path.dirname(__file__), 'data')
        favicon = os.path.join(mopidy_dir, 'favicon.png')

        config = {
            b'/': {
                'tools.staticdir.on': True,
                'tools.staticdir.index': 'index.html',
                'tools.staticdir.dir': static_dir,
            },
            b'/favicon.ico': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': favicon,
            },
            b'/mopidy': {
                'tools.staticdir.on': True,
                'tools.staticdir.index': 'mopidy.html',
                'tools.staticdir.dir': mopidy_dir,
            },
            b'/mopidy/ws': {
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

        if self.zeroconf_name:
            self.zeroconf_service = zeroconf.Zeroconf(
                stype='_http._tcp', name=self.zeroconf_name,
                host=self.hostname, port=self.port)

            if self.zeroconf_service.publish():
                logger.info('Registered HTTP with Zeroconf as "%s"',
                            self.zeroconf_service.name)
            else:
                logger.warning('Registering HTTP with Zeroconf failed.')

    def on_stop(self):
        if self.zeroconf_service:
            self.zeroconf_service.unpublish()

        logger.debug('Stopping HTTP server')
        cherrypy.engine.exit()
        logger.info('Stopped HTTP server')

    def on_event(self, name, **data):
        event = data
        event['event'] = name
        message = json.dumps(event, cls=models.ModelJSONEncoder)
        cherrypy.engine.publish('websocket-broadcast', TextMessage(message))


class RootResource(object):
    pass


class MopidyResource(object):
    pass
