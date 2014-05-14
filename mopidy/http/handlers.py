from __future__ import unicode_literals

import logging

import tornado.escape
import tornado.web
import tornado.websocket

from mopidy import __version__, core, models
from mopidy.utils import jsonrpc


logger = logging.getLogger(__name__)


def construct_rpc(actor):
    inspector = jsonrpc.JsonRpcInspector(
        objects={
            'core.get_uri_schemes': core.Core.get_uri_schemes,
            'core.get_version': core.Core.get_version,
            'core.library': core.LibraryController,
            'core.playback': core.PlaybackController,
            'core.playlists': core.PlaylistsController,
            'core.tracklist': core.TracklistController,
        })
    return jsonrpc.JsonRpcWrapper(
        objects={
            'core.describe': inspector.describe,
            'core.get_uri_schemes': actor.core.get_uri_schemes,
            'core.get_version': actor.core.get_version,
            'core.library': actor.core.library,
            'core.playback': actor.core.playback,
            'core.playlists': actor.core.playlists,
            'core.tracklist': actor.core.tracklist,
        },
        decoders=[models.model_json_decoder],
        encoders=[models.ModelJSONEncoder]
    )


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, actor):
        self.actor = actor
        self.jsonrpc = construct_rpc(actor)

    @classmethod
    def broadcast(cls, clients, msg):
        for client in clients:
            client.write_message(msg)

    def open(self):
        self.set_nodelay(True)
        self.actor.websocket_clients.add(self)
        logger.debug(
            'New WebSocket connection from %s', self.request.remote_ip)

    def on_close(self):
        self.actor.websocket_clients.discard(self)
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
                tornado.escape.native_str(message)
            )
            if response and self.write_message(response):
                logger.debug(
                    'Sent WebSocket message to %s: %r',
                    self.request.remote_ip, response)
        except Exception as e:
            logger.error('WebSocket request error:', e)
            self.close()


class JsonRpcHandler(tornado.web.RequestHandler):
    def initialize(self, actor):
        self.jsonrpc = construct_rpc(actor)

    def head(self):
        self.set_extra_headers()
        self.finish()

    def post(self):
        data = self.request.body

        if not data:
            return
        logger.debug('Received RPC message from %s: %r',
                     self.request.remote_ip, data)
        try:
            self.set_extra_headers()
            response = self.jsonrpc.handle_json(
                tornado.escape.native_str(data))
            if response and self.write(response):
                logger.debug('Sent RPC message to %s: %r',
                             self.request.remote_ip, response)
        except Exception as e:
            logger.error('HTTP JSON-RPC request error:', e)
            self.write_error(500)

    def set_extra_headers(self):
        self.set_header('Accept', 'application/json')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('X-Mopidy-Version', __version__.encode(
            'utf-8'))
        self.set_header('Content-Type', 'application/json; utf-8')
