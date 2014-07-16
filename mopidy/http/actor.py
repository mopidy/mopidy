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
from mopidy.utils import formatting


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
        self.zeroconf_http = None
        self.zeroconf_mopidy_http = None

        self.app = None

    def on_start(self):
        threading.Thread(target=self._startup).start()

        if self.zeroconf_name:
            self.zeroconf_http = zeroconf.Zeroconf(
                stype='_http._tcp', name=self.zeroconf_name,
                host=self.hostname, port=self.port)
            self.zeroconf_mopidy_http = zeroconf.Zeroconf(
                stype='_mopidy-http._tcp', name=self.zeroconf_name,
                host=self.hostname, port=self.port)
            self.zeroconf_http.publish()
            self.zeroconf_mopidy_http.publish()

    def on_stop(self):
        if self.zeroconf_http:
            self.zeroconf_http.unpublish()
        if self.zeroconf_mopidy_http:
            self.zeroconf_mopidy_http.unpublish()

        tornado.ioloop.IOLoop.instance().add_callback(self._shutdown)

    def _startup(self):
        logger.debug('Starting HTTP server')
        self.app = tornado.web.Application(self._get_request_handlers())
        self.app.listen(self.port,
                        self.hostname if self.hostname != '::' else None)
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
        if static_dir and not os.path.exists(static_dir):
            logger.warning(
                'Configured http/static_dir %s does not exist. '
                'Falling back to default HTTP handler.', static_dir)
            static_dir = None
        if static_dir:
            request_handlers.append((r'/(.*)', handlers.StaticFileHandler, {
                'path': self.config['http']['static_dir'],
                'default_filename': 'index.html',
            }))
        else:
            request_handlers.append((r'/', tornado.web.RedirectHandler, {
                'url': '/mopidy/',
                'permanent': False,
            }))

        logger.debug(
            'HTTP routes from extensions: %s',
            formatting.indent('\n'.join(
                '%r: %r' % (r[0], r[1]) for r in request_handlers)))
        return request_handlers

    def _get_app_request_handlers(self):
        result = []
        for app in self.apps:
            result.append((
                r'/%s' % app['name'],
                handlers.AddSlashHandler
            ))
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
                r'/%s' % static['name'],
                handlers.AddSlashHandler
            ))
            result.append((
                r'/%s/(.*)' % static['name'],
                handlers.StaticFileHandler,
                {
                    'path': static['path'],
                    'default_filename': 'index.html'
                }
            ))
            logger.debug('Loaded static HTTP extension: %s', static['name'])
        return result
