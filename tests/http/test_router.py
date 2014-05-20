from __future__ import unicode_literals

import os
import unittest

import mock

from tornado.escape import json_decode, json_encode, to_unicode
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

import mopidy
from mopidy import http
from mopidy.http import handlers


try:
    import tornado
except ImportError:
    tornado = False

if tornado:
    from mopidy.http import actor


class TestRouter(http.Router):
    name = 'test'
    static_file_path = os.path.join(os.path.dirname(__file__), 'static')


class TestRouterMissingPath(http.Router):
    name = 'test'


class TestRouterMissingName(http.Router):
    static_file_path = os.path.join(os.path.dirname(__file__), 'static')


@unittest.skipUnless(tornado, 'tornado is missing')
class HttpRouterTest(unittest.TestCase):
    def setUp(self):
        self.config = {
            'http': {
                'hostname': '127.0.0.1',
                'port': 6680,
                'static_dir': None,
                'zeroconf': '',
            }
        }
        self.http = actor.HttpFrontend(config=self.config, core=mock.Mock())

    def test_default_router(self):
        router = TestRouter(self.config)

        (pattern, handler_class, kwargs) = router.get_request_handlers()[0]

        self.assertEqual(pattern, r'/test/(.*)')
        self.assertIs(handler_class, handlers.StaticFileHandler)
        self.assertEqual(
            kwargs['path'], os.path.join(os.path.dirname(__file__), 'static'))

    def test_default_router_missing_name(self):
        with self.assertRaises(ValueError):
            TestRouterMissingName(self.config)

    def test_default_router_missing_path(self):
        with self.assertRaises(ValueError):
            TestRouterMissingPath(self.config).get_request_handlers()

    def test_default_uri_helper(self):
        router = TestRouter(self.config)
        self.assertEqual('http://127.0.0.1:6680/test/', router.get_root_url())


class StaticFileHandlerTest(AsyncHTTPTestCase):
    def get_app(self):
        app = Application([(r'/(.*)', handlers.StaticFileHandler, {
            'path': os.path.dirname(__file__),
            'default_filename': 'test_router.py'
        })])
        return app

    def test_static_handler(self):
        response = self.fetch('/test_router.py', method='GET')
        self.assertEqual(response.headers['X-Mopidy-Version'],
                         mopidy.__version__)
        self.assertEqual(response.headers['Cache-Control'],
                         'no-cache')

    def test_static_default_filename(self):
        response = self.fetch('/', method='GET')
        self.assertEqual(response.headers['X-Mopidy-Version'],
                         mopidy.__version__)
        self.assertEqual(response.headers['Cache-Control'],
                         'no-cache')


class DefaultHTTPServerTest(AsyncHTTPTestCase):
    def get_app(self):
        config = {
            'http': {
                'hostname': '127.0.0.1',
                'port': 6680,
                'static_dir': None,
                'zeroconf': '',
            }
        }
        core = mock.Mock()
        core.get_version = mock.MagicMock(name='get_version')
        core.get_version.return_value = mopidy.__version__

        actor_http = actor.HttpFrontend(config=config, core=core)
        return Application(actor_http._create_routes())

    def test_root_should_return_index(self):
        response = self.fetch('/', method='GET')
        self.assertIn(
            'Static content serving',
            to_unicode(response.body)
        )
        self.assertEqual(response.headers['X-Mopidy-Version'],
                         mopidy.__version__)
        self.assertEqual(response.headers['Cache-Control'],
                         'no-cache')

    def test_mopidy_should_return_index(self):
        response = self.fetch('/mopidy/', method='GET')
        self.assertIn(
            'Here you can see events arriving from Mopidy in real time:',
            to_unicode(response.body)
        )
        self.assertEqual(response.headers['X-Mopidy-Version'],
                         mopidy.__version__)
        self.assertEqual(response.headers['Cache-Control'],
                         'no-cache')

    def test_should_return_js(self):
        response = self.fetch('/mopidy/mopidy.js', method='GET')
        self.assertIn(
            'function Mopidy',
            to_unicode(response.body)
        )
        self.assertEqual(response.headers['X-Mopidy-Version'],
                         mopidy.__version__)
        self.assertEqual(response.headers['Cache-Control'],
                         'no-cache')

    def test_should_return_ws(self):
        response = self.fetch('/mopidy/ws', method='GET')
        self.assertEqual(
            'Can "Upgrade" only to "WebSocket".',
            to_unicode(response.body)
        )

    def test_should_return_ws_old(self):
        response = self.fetch('/mopidy/ws/', method='GET')
        self.assertEqual(
            'Can "Upgrade" only to "WebSocket".',
            to_unicode(response.body)
        )

    def test_should_return_rpc_error(self):
        cmd = json_encode({
            'action': 'get_version'
        })
        response = self.fetch('/mopidy/rpc', method='POST', body=cmd)
        self.assertEqual(
            {'jsonrpc': '2.0', 'id': None, 'error':
                {'message': 'Invalid Request', 'code': -32600,
                 'data': '"jsonrpc" member must be included'}},
            json_decode(response.body)
        )

    def test_should_return_parse_error(self):
        cmd = '{[[[]}'
        response = self.fetch('/mopidy/rpc', method='POST', body=cmd)
        self.assertEqual(
            {'jsonrpc': '2.0', 'id': None, 'error':
                {'message': 'Parse error', 'code': -32700}},
            json_decode(response.body)
        )

    def test_should_return_mopidy_version(self):
        cmd = json_encode({
            'method': 'core.get_version',
            'params': [],
            'jsonrpc': '2.0',
            'id': 1
        })
        response = self.fetch('/mopidy/rpc', method='POST', body=cmd)
        self.assertEqual(
            {'jsonrpc': '2.0', 'id': 1, 'result': mopidy.__version__},
            json_decode(response.body)
        )

    def test_should_return_extra_headers(self):
        response = self.fetch('/mopidy/rpc', method='HEAD')
        self.assertIn('Accept', response.headers)
        self.assertIn('X-Mopidy-Version', response.headers)
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('Content-Type', response.headers)
