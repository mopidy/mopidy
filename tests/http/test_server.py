from __future__ import absolute_import, unicode_literals

import os

import mock

import tornado.testing
import tornado.wsgi

import mopidy
from mopidy.http import actor, handlers


class HttpServerTest(tornado.testing.AsyncHTTPTestCase):

    def get_config(self):
        return {
            'http': {
                'hostname': '127.0.0.1',
                'port': 6680,
                'static_dir': None,
                'zeroconf': '',
            }
        }

    def get_app(self):
        core = mock.Mock()
        core.get_version = mock.MagicMock(name='get_version')
        core.get_version.return_value = mopidy.__version__

        testapps = [dict(name='testapp')]
        teststatics = [dict(name='teststatic')]

        apps = [{
            'name': 'mopidy',
            'factory': handlers.make_mopidy_app_factory(testapps, teststatics),
        }]

        http_server = actor.HttpServer(
            config=self.get_config(), core=core, sockets=[],
            apps=apps, statics=[])

        return tornado.web.Application(http_server._get_request_handlers())


class RootRedirectTest(HttpServerTest):

    def test_should_redirect_to_mopidy_app(self):
        response = self.fetch('/', method='GET', follow_redirects=False)

        self.assertEqual(response.code, 302)
        self.assertEqual(response.headers['Location'], '/mopidy/')


class LegacyStaticDirAppTest(HttpServerTest):

    def get_config(self):
        config = super(LegacyStaticDirAppTest, self).get_config()
        config['http']['static_dir'] = os.path.dirname(__file__)
        return config

    def test_should_return_index(self):
        response = self.fetch('/', method='GET', follow_redirects=False)

        self.assertEqual(response.code, 404, 'No index.html in this dir')

    def test_should_return_static_files(self):
        response = self.fetch('/test_server.py', method='GET')

        self.assertIn(
            'test_should_return_static_files',
            tornado.escape.to_unicode(response.body))
        self.assertEqual(
            response.headers['X-Mopidy-Version'], mopidy.__version__)
        self.assertEqual(response.headers['Cache-Control'], 'no-cache')


class MopidyAppTest(HttpServerTest):

    def test_should_return_index(self):
        response = self.fetch('/mopidy/', method='GET')
        body = tornado.escape.to_unicode(response.body)

        self.assertIn(
            'This web server is a part of the Mopidy music server.', body)
        self.assertIn('testapp', body)
        self.assertIn('teststatic', body)
        self.assertEqual(
            response.headers['X-Mopidy-Version'], mopidy.__version__)
        self.assertEqual(response.headers['Cache-Control'], 'no-cache')

    def test_without_slash_should_redirect(self):
        response = self.fetch('/mopidy', method='GET', follow_redirects=False)

        self.assertEqual(response.code, 301)
        self.assertEqual(response.headers['Location'], '/mopidy/')

    def test_should_return_static_files(self):
        response = self.fetch('/mopidy/mopidy.js', method='GET')

        self.assertIn(
            'function Mopidy',
            tornado.escape.to_unicode(response.body))
        self.assertEqual(
            response.headers['X-Mopidy-Version'], mopidy.__version__)
        self.assertEqual(response.headers['Cache-Control'], 'no-cache')


class MopidyWebSocketHandlerTest(HttpServerTest):

    def test_should_return_ws(self):
        response = self.fetch('/mopidy/ws', method='GET')

        self.assertEqual(
            'Can "Upgrade" only to "WebSocket".',
            tornado.escape.to_unicode(response.body))

    def test_should_return_ws_old(self):
        response = self.fetch('/mopidy/ws/', method='GET')

        self.assertEqual(
            'Can "Upgrade" only to "WebSocket".',
            tornado.escape.to_unicode(response.body))


class MopidyRPCHandlerTest(HttpServerTest):

    def test_should_return_rpc_error(self):
        cmd = tornado.escape.json_encode({'action': 'get_version'})

        response = self.fetch('/mopidy/rpc', method='POST', body=cmd)

        self.assertEqual(
            {'jsonrpc': '2.0', 'id': None, 'error':
                {'message': 'Invalid Request', 'code': -32600,
                 'data': '"jsonrpc" member must be included'}},
            tornado.escape.json_decode(response.body))

    def test_should_return_parse_error(self):
        cmd = '{[[[]}'

        response = self.fetch('/mopidy/rpc', method='POST', body=cmd)

        self.assertEqual(
            {'jsonrpc': '2.0', 'id': None, 'error':
                {'message': 'Parse error', 'code': -32700}},
            tornado.escape.json_decode(response.body))

    def test_should_return_mopidy_version(self):
        cmd = tornado.escape.json_encode({
            'method': 'core.get_version',
            'params': [],
            'jsonrpc': '2.0',
            'id': 1,
        })

        response = self.fetch('/mopidy/rpc', method='POST', body=cmd)

        self.assertEqual(
            {'jsonrpc': '2.0', 'id': 1, 'result': mopidy.__version__},
            tornado.escape.json_decode(response.body))

    def test_should_return_extra_headers(self):
        response = self.fetch('/mopidy/rpc', method='HEAD')

        self.assertIn('Accept', response.headers)
        self.assertIn('X-Mopidy-Version', response.headers)
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('Content-Type', response.headers)


class HttpServerWithStaticFilesTest(tornado.testing.AsyncHTTPTestCase):

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

        statics = [dict(name='static', path=os.path.dirname(__file__))]

        http_server = actor.HttpServer(
            config=config, core=core, sockets=[], apps=[], statics=statics)

        return tornado.web.Application(http_server._get_request_handlers())

    def test_without_slash_should_redirect(self):
        response = self.fetch('/static', method='GET', follow_redirects=False)

        self.assertEqual(response.code, 301)
        self.assertEqual(response.headers['Location'], '/static/')

    def test_can_serve_static_files(self):
        response = self.fetch('/static/test_server.py', method='GET')

        self.assertEqual(200, response.code)
        self.assertEqual(
            response.headers['X-Mopidy-Version'], mopidy.__version__)
        self.assertEqual(
            response.headers['Cache-Control'], 'no-cache')


def wsgi_app_factory(config, core):

    def wsgi_app(environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return ['Hello, world!\n']

    return [
        ('(.*)', tornado.web.FallbackHandler, {
            'fallback': tornado.wsgi.WSGIContainer(wsgi_app),
        }),
    ]


class HttpServerWithWsgiAppTest(tornado.testing.AsyncHTTPTestCase):

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

        apps = [{
            'name': 'wsgi',
            'factory': wsgi_app_factory,
        }]

        http_server = actor.HttpServer(
            config=config, core=core, sockets=[], apps=apps, statics=[])

        return tornado.web.Application(http_server._get_request_handlers())

    def test_without_slash_should_redirect(self):
        response = self.fetch('/wsgi', method='GET', follow_redirects=False)

        self.assertEqual(response.code, 301)
        self.assertEqual(response.headers['Location'], '/wsgi/')

    def test_can_wrap_wsgi_apps(self):
        response = self.fetch('/wsgi/', method='GET')

        self.assertEqual(200, response.code)
        self.assertIn(
            'Hello, world!', tornado.escape.to_unicode(response.body))
