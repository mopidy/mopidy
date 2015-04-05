from __future__ import absolute_import, unicode_literals

import os

import mock

import tornado.testing
import tornado.web
import tornado.websocket

import mopidy
from mopidy.http import handlers


class StaticFileHandlerTest(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return tornado.web.Application([
            (r'/(.*)', handlers.StaticFileHandler, {
                'path': os.path.dirname(__file__),
                'default_filename': 'test_handlers.py'
            })
        ])

    def test_static_handler(self):
        response = self.fetch('/test_handlers.py', method='GET')

        self.assertEqual(200, response.code)
        self.assertEqual(
            response.headers['X-Mopidy-Version'], mopidy.__version__)
        self.assertEqual(
            response.headers['Cache-Control'], 'no-cache')

    def test_static_default_filename(self):
        response = self.fetch('/', method='GET')

        self.assertEqual(200, response.code)
        self.assertEqual(
            response.headers['X-Mopidy-Version'], mopidy.__version__)
        self.assertEqual(
            response.headers['Cache-Control'], 'no-cache')


# We aren't bothering with skipIf as then we would need to "backport" gen_test
if hasattr(tornado.websocket, 'websocket_connect'):
    class WebSocketHandlerTest(tornado.testing.AsyncHTTPTestCase):

        def get_app(self):
            self.core = mock.Mock()
            return tornado.web.Application([
                (r'/ws/?', handlers.WebSocketHandler, {'core': self.core})
            ])

        def connection(self):
            url = self.get_url('/ws').replace('http', 'ws')
            return tornado.websocket.websocket_connect(url, self.io_loop)

        @tornado.testing.gen_test
        def test_invalid_json_rpc_request_doesnt_crash_handler(self):
            # An uncaught error would result in no message, so this is just a
            # simplistic test to verify this.
            conn = yield self.connection()
            conn.write_message('invalid request')
            message = yield conn.read_message()
            self.assertTrue(message)

        @tornado.testing.gen_test
        def test_broadcast_makes_it_to_client(self):
            conn = yield self.connection()
            handlers.WebSocketHandler.broadcast('message')
            message = yield conn.read_message()
            self.assertEqual(message, 'message')

        @tornado.testing.gen_test
        def test_broadcast_to_client_that_just_closed_connection(self):
            conn = yield self.connection()
            conn.stream.close()
            handlers.WebSocketHandler.broadcast('message')

        @tornado.testing.gen_test
        def test_broadcast_to_client_without_ws_connection_present(self):
            yield self.connection()
            # Tornado checks for ws_connection and raises WebSocketClosedError
            # if it is missing, this test case simulates winning a race were
            # this has happened but we have not yet been removed from clients.
            for client in handlers.WebSocketHandler.clients:
                client.ws_connection = None
            handlers.WebSocketHandler.broadcast('message')
