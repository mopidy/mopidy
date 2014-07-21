from __future__ import unicode_literals

import os

import tornado.testing
import tornado.web

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
