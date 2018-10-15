from __future__ import absolute_import, unicode_literals

import functools
import logging
import os

import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket

import mopidy
from mopidy import core, models
from mopidy.compat import urllib
from mopidy.internal import encoding, jsonrpc


logger = logging.getLogger(__name__)


def make_mopidy_app_factory(apps, statics):
    def mopidy_app_factory(config, core):
        if not config['http']['csrf_protection']:
            logger.warn(
                'HTTP Cross-Site Request Forgery protection is disabled')
        allowed_origins = {
            x.lower() for x in config['http']['allowed_origins'] if x
        }
        return [
            (r'/ws/?', WebSocketHandler, {
                'core': core,
                'allowed_origins': allowed_origins,
                'csrf_protection': config['http']['csrf_protection'],
            }),
            (r'/rpc', JsonRpcHandler, {
                'core': core,
                'allowed_origins': allowed_origins,
                'csrf_protection': config['http']['csrf_protection'],
            }),
            (r'/(.+)', StaticFileHandler, {
                'path': os.path.join(os.path.dirname(__file__), 'data'),
            }),
            (r'/', ClientListHandler, {
                'apps': apps,
                'statics': statics,
            }),
        ]
    return mopidy_app_factory


def make_jsonrpc_wrapper(core_actor):
    inspector = jsonrpc.JsonRpcInspector(
        objects={
            'core.get_uri_schemes': core.Core.get_uri_schemes,
            'core.get_version': core.Core.get_version,
            'core.history': core.HistoryController,
            'core.library': core.LibraryController,
            'core.mixer': core.MixerController,
            'core.playback': core.PlaybackController,
            'core.playlists': core.PlaylistsController,
            'core.tracklist': core.TracklistController,
        })
    return jsonrpc.JsonRpcWrapper(
        objects={
            'core.describe': inspector.describe,
            'core.get_uri_schemes': core_actor.get_uri_schemes,
            'core.get_version': core_actor.get_version,
            'core.history': core_actor.history,
            'core.library': core_actor.library,
            'core.mixer': core_actor.mixer,
            'core.playback': core_actor.playback,
            'core.playlists': core_actor.playlists,
            'core.tracklist': core_actor.tracklist,
        },
        decoders=[models.model_json_decoder],
        encoders=[models.ModelJSONEncoder]
    )


def _send_broadcast(client, msg):
    # We could check for client.ws_connection, but we don't really
    # care why the broadcast failed, we just want the rest of them
    # to succeed, so catch everything.
    try:
        client.write_message(msg)
    except Exception as e:
        error_msg = encoding.locale_decode(e)
        logger.debug('Broadcast of WebSocket message to %s failed: %s',
                     client.request.remote_ip, error_msg)
        # TODO: should this do the same cleanup as the on_message code?


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    # XXX This set is shared by all WebSocketHandler objects. This isn't
    # optimal, but there's currently no use case for having more than one of
    # these anyway.
    clients = set()

    @classmethod
    def broadcast(cls, msg):
        loop = tornado.ioloop.IOLoop.current()

        # This can be called from outside the Tornado ioloop, so we need to
        # safely cross the thread boundary by adding a callback to the loop.
        for client in cls.clients:
            # One callback per client to keep time we hold up the loop short
            loop.add_callback(functools.partial(_send_broadcast, client, msg))

    def initialize(self, core, allowed_origins, csrf_protection):
        self.jsonrpc = make_jsonrpc_wrapper(core)
        self.allowed_origins = allowed_origins
        self.csrf_protection = csrf_protection

    def open(self):
        self.set_nodelay(True)
        self.clients.add(self)
        logger.debug(
            'New WebSocket connection from %s', self.request.remote_ip)

    def on_close(self):
        self.clients.discard(self)
        logger.debug(
            'Closed WebSocket connection from %s',
            self.request.remote_ip)

    def on_message(self, message):
        if not message:
            return

        logger.debug(
            'Received WebSocket message from %s: %r',
            self.request.remote_ip, message)

        try:
            response = self.jsonrpc.handle_json(
                tornado.escape.native_str(message))
            if response and self.write_message(response):
                logger.debug(
                    'Sent WebSocket message to %s: %r',
                    self.request.remote_ip, response)
        except Exception as e:
            error_msg = encoding.locale_decode(e)
            logger.error('WebSocket request error: %s', error_msg)
            self.close()

    def check_origin(self, origin):
        if not self.csrf_protection:
            return True
        return check_origin(origin, self.request.headers, self.allowed_origins)


def set_mopidy_headers(request_handler):
    request_handler.set_header('Cache-Control', 'no-cache')
    request_handler.set_header(
        'X-Mopidy-Version', mopidy.__version__.encode('utf-8'))


def check_origin(origin, request_headers, allowed_origins):
    if origin is None:
        logger.warn('HTTP request denied for missing Origin header')
        return False
    allowed_origins.add(request_headers.get('Host'))
    parsed_origin = urllib.parse.urlparse(origin).netloc.lower()
    # Some frameworks (e.g. Apache Cordova) use local files. Requests from
    # these files don't really have a sensible Origin so the browser sets the
    # header to something like 'file://' or 'null'. This results here in an
    # empty parsed_origin which we choose to allow.
    if parsed_origin and parsed_origin not in allowed_origins:
        logger.warn('HTTP request denied for Origin "%s"', origin)
        return False
    return True


class JsonRpcHandler(tornado.web.RequestHandler):

    def initialize(self, core, allowed_origins, csrf_protection):
        self.jsonrpc = make_jsonrpc_wrapper(core)
        self.allowed_origins = allowed_origins
        self.csrf_protection = csrf_protection

    def head(self):
        self.set_extra_headers()
        self.finish()

    def post(self):
        if self.csrf_protection:
            content_type = self.request.headers.get('Content-Type', '')
            if content_type != 'application/json':
                self.set_status(415, 'Content-Type must be application/json')
                return

        data = self.request.body
        if not data:
            return

        logger.debug(
            'Received RPC message from %s: %r', self.request.remote_ip, data)

        try:
            self.set_extra_headers()
            response = self.jsonrpc.handle_json(
                tornado.escape.native_str(data))
            if response and self.write(response):
                logger.debug(
                    'Sent RPC message to %s: %r',
                    self.request.remote_ip, response)
        except Exception as e:
            logger.error('HTTP JSON-RPC request error: %s', e)
            self.write_error(500)

    def set_extra_headers(self):
        set_mopidy_headers(self)
        self.set_header('Accept', 'application/json')
        self.set_header('Content-Type', 'application/json; utf-8')

    def options(self):
        if self.csrf_protection:
            origin = self.request.headers.get('Origin')
            if not check_origin(origin, self.request.headers,
                                self.allowed_origins):
                self.set_status(403, 'Access denied for origin %s' % origin)
                return

            self.set_header('Access-Control-Allow-Origin', '%s' % origin)
            self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        self.set_status(204)
        self.finish()


class ClientListHandler(tornado.web.RequestHandler):

    def initialize(self, apps, statics):
        self.apps = apps
        self.statics = statics

    def get_template_path(self):
        return os.path.dirname(__file__)

    def get(self):
        set_mopidy_headers(self)

        names = set()
        for app in self.apps:
            names.add(app['name'])
        for static in self.statics:
            names.add(static['name'])
        names.discard('mopidy')

        self.render('data/clients.html', apps=sorted(list(names)))


class StaticFileHandler(tornado.web.StaticFileHandler):

    def set_extra_headers(self, path):
        set_mopidy_headers(self)


class AddSlashHandler(tornado.web.RequestHandler):

    @tornado.web.addslash
    def prepare(self):
        return super(AddSlashHandler, self).prepare()
