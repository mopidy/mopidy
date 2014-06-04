from __future__ import unicode_literals

import os
import unittest

import mock

from mopidy import http


class TestRouter(http.Router):
    name = 'test'
    static_file_path = os.path.join(os.path.dirname(__file__), 'static')


class TestRouterMissingName(http.Router):
    pass


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

    def test_undefined_name_raises_error(self):
        with self.assertRaises(ValueError):
            TestRouterMissingName(self.config, self.core)

    def test_undefined_request_handlers_raises_error(self):
        router = TestRouter(self.config, self.core)

        with self.assertRaises(NotImplementedError):
            router.get_request_handlers()
