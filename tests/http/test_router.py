from __future__ import unicode_literals

import os
import unittest

import mock

from mopidy import http
from mopidy.http import handlers


class TestRouter(http.Router):
    name = 'test'
    static_file_path = os.path.join(os.path.dirname(__file__), 'static')


class TestRouterMissingPath(http.Router):
    name = 'test'


class TestRouterMissingName(http.Router):
    static_file_path = os.path.join(os.path.dirname(__file__), 'static')


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
        self.core = mock.Mock()

    def test_keeps_reference_to_config_and_core(self):
        router = TestRouter(self.config, self.core)

        self.assertIs(router.config, self.config)
        self.assertIs(router.core, self.core)

    def test_default_request_handlers(self):
        router = TestRouter(self.config, self.core)

        (pattern, handler_class, kwargs) = router.get_request_handlers()[0]

        self.assertEqual(pattern, r'/test/(.*)')
        self.assertIs(handler_class, handlers.StaticFileHandler)
        self.assertEqual(
            kwargs['path'], os.path.join(os.path.dirname(__file__), 'static'))

    def test_default_router_missing_name(self):
        with self.assertRaises(ValueError):
            TestRouterMissingName(self.config, self.core)

    def test_default_router_missing_path(self):
        router = TestRouterMissingPath(self.config, self.core)

        with self.assertRaises(ValueError):
            router.get_request_handlers()

    def test_get_root_url(self):
        router = TestRouter(self.config, self.core)

        self.assertEqual('http://127.0.0.1:6680/test/', router.get_root_url())
