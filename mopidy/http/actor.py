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
    apps = []
    statics = []

    def __init__(self, config, core):
        super(HttpFrontend, self).__init__()
        self.config = config
        self.core = core

        self.hostname = config['http']['hostname']
        self.port = config['http']['port']
        self.zeroconf_name = config['http']['zeroconf']
        self.zeroconf_service = None
        self.app = None

    def on_start(self):
        threading.Thread(target=self._startup).start()
        self._publish_zeroconf()

    def on_stop(self):
        self._unpublish_zeroconf()
        tornado.ioloop.IOLoop.instance().add_callback(self._shutdown)

    def _startup(self):
        logger.debug('Starting HTTP server')
        self.app = tornado.web.Application(self._get_request_handlers())
        self.app.listen(self.port, self.hostname)
        logger.info(
            'HTTP server running at http://%s:%s', self.hostname, self.port)
        tornado.ioloop.IOLoop.instance().start()

    def _shutdown(self):
        logger.debug('Stopping HTTP server')
        tornado.ioloop.IOLoop.instance().stop()
        logger.debug('Stopped HTTP server')

    def on_event(self, name, **data):
        event = data
        event['event'] = name
        message = json.dumps(event, cls=models.ModelJSONEncoder)
        handlers.WebSocketHandler.broadcast(message)

    def _get_request_handlers(self):
        request_handlers = []

        request_handlers.extend(self._get_app_request_handlers())
        request_handlers.extend(self._get_static_request_handlers())

        # Either default Mopidy or user defined path to files
        static_dir = self.config['http']['static_dir']
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        root_handler = (r'/(.*)', handlers.StaticFileHandler, {
            'path': static_dir if static_dir else data_dir,
            'default_filename': 'index.html'
        })
        request_handlers.append(root_handler)

        logger.debug(
            'HTTP routes from extensions: %s',
            list((l[0], l[1]) for l in request_handlers))
        return request_handlers

    def _get_app_request_handlers(self):
        result = []
        for app in self.apps:
            request_handlers = app['factory'](self.config, self.core)
            for handler in request_handlers:
                handler = list(handler)
                handler[0] = '/%s%s' % (app['name'], handler[0])
                result.append(tuple(handler))
            logger.debug('Loaded HTTP extension: %s', app['name'])
        return result

    def _get_static_request_handlers(self):
        result = []
        for static in self.statics:
            result.append((
                r'/%s/(.*)' % static['name'],
                handlers.StaticFileHandler,
                {
                    'path': static['path'],
                    'default_filename': 'index.html'
                }
            ))
            logger.debug('Loaded HTTP extension: %s', static['name'])
        return result

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
