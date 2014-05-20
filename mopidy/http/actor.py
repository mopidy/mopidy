from __future__ import unicode_literals

import json
import logging
import os
import threading

import pykka

import tornado.ioloop
import tornado.web
import tornado.websocket

from mopidy import models, zeroconf
from mopidy.core import CoreListener
from mopidy.http import handlers


logger = logging.getLogger(__name__)


class HttpFrontend(pykka.ThreadingActor, CoreListener):
    routers = []

    def __init__(self, config, core):
        super(HttpFrontend, self).__init__()
        self.config = config
        self.core = core

        self.hostname = config['http']['hostname']
        self.port = config['http']['port']
        self.zeroconf_name = config['http']['zeroconf']
        self.zeroconf_service = None
        self.app = None
        self.websocket_clients = set()

    def _load_extensions(self):
        request_handlers = []
        for router_class in self.routers:
            router = router_class(self.config)
            request_handlers.extend(router.get_request_handlers())
            logger.info(
                'Loaded HTTP extension: %s', router_class.__name__)
        return request_handlers

    def _create_routes(self):
        mopidy_dir = os.path.join(os.path.dirname(__file__), 'data')
        static_dir = self.config['http']['static_dir']

        # either default mopidy or user defined path to files
        primary_dir = (r'/(.*)', handlers.StaticFileHandler, {
            'path': static_dir if static_dir else mopidy_dir,
            'default_filename': 'index.html'
        })

        routes = self._load_extensions()
        logger.debug(
            'HTTP routes from extensions: %s',
            list((l[0], l[1]) for l in routes)
        )

        # TODO: Dynamically define all endpoints
        routes.extend([
            (r'/mopidy/ws/?', handlers.WebSocketHandler, {'actor': self}),
            (r'/mopidy/rpc', handlers.JsonRpcHandler, {'actor': self}),
            (r'/mopidy/(.*)', handlers.StaticFileHandler, {
                'path': mopidy_dir, 'default_filename': 'mopidy.html'
            }),
            primary_dir,
        ])
        return routes

    def on_start(self):
        threading.Thread(target=self._startup).start()
        self._publish_zeroconf()

    def on_stop(self):
        self._unpublish_zeroconf()
        tornado.ioloop.IOLoop.instance().add_callback(self._shutdown)

    def _startup(self):
        logger.debug('Starting HTTP server')
        self.app = tornado.web.Application(self._create_routes())
        self.app.listen(self.port, self.hostname)
        logger.info(
            'HTTP server running at http://%s:%s', self.hostname, self.port)
        tornado.ioloop.IOLoop.instance().start()

    def _shutdown(self):
        logger.debug('Stopping HTTP server')
        tornado.ioloop.IOLoop.instance().stop()
        logger.info('Stopped HTTP server')

    def on_event(self, name, **data):
        event = data
        event['event'] = name
        message = json.dumps(event, cls=models.ModelJSONEncoder)
        handlers.WebSocketHandler.broadcast(self.websocket_clients, message)

    def _publish_zeroconf(self):
        if not self.zeroconf_name:
            return

        self.zeroconf_http_service = zeroconf.Zeroconf(
            stype='_http._tcp', name=self.zeroconf_name,
            host=self.hostname, port=self.port)

        if self.zeroconf_http_service.publish():
            logger.debug(
                'Registered HTTP with Zeroconf as "%s"',
                self.zeroconf_http_service.name)
        else:
            logger.debug('Registering HTTP with Zeroconf failed.')

        self.zeroconf_mopidy_http_service = zeroconf.Zeroconf(
            stype='_mopidy-http._tcp', name=self.zeroconf_name,
            host=self.hostname, port=self.port)

        if self.zeroconf_mopidy_http_service.publish():
            logger.debug(
                'Registered Mopidy-HTTP with Zeroconf as "%s"',
                self.zeroconf_mopidy_http_service.name)
        else:
            logger.debug('Registering Mopidy-HTTP with Zeroconf failed.')

    def _unpublish_zeroconf(self):
        if self.zeroconf_http_service:
            self.zeroconf_http_service.unpublish()

        if self.zeroconf_mopidy_http_service:
            self.zeroconf_mopidy_http_service.unpublish()
