from __future__ import absolute_import, unicode_literals

import functools
import logging
import os
import socket

import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket

import mopidy
from mopidy import core, models
from mopidy.internal import encoding, jsonrpc


logger = logging.getLogger(__name__)


def make_mopidy_app_factory(apps, statics):
    def mopidy_app_factory(config, core):
        return [
            (r'/ws/?', WebSocketHandler, {
                'core': core,
            }),
            (r'/rpc', JsonRpcHandler, {
                'core': core,
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

    def initialize(self, core):
        self.jsonrpc = make_jsonrpc_wrapper(core)

    def open(self):
        if hasattr(self, 'set_nodelay'):
            # New in Tornado 3.1
            self.set_nodelay(True)
        else:
            self.stream.socket.setsockopt(
                socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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
        # Allow cross-origin WebSocket connections, like Tornado before 4.0
        # defaulted to.
        return True


def set_mopidy_headers(request_handler):
    request_handler.set_header('Cache-Control', 'no-cache')
    request_handler.set_header(
        'X-Mopidy-Version', mopidy.__version__.encode('utf-8'))


class JsonRpcHandler(tornado.web.RequestHandler):

    def initialize(self, core):
        self.jsonrpc = make_jsonrpc_wrapper(core)

    def head(self):
        self.set_extra_headers()
        self.finish()

    def post(self):
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
