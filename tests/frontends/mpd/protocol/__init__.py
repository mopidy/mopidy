from __future__ import unicode_literals

import mock
import unittest

import pykka

from mopidy import core
from mopidy.backends import dummy
from mopidy.frontends.mpd import session


class MockConnection(mock.Mock):
    def __init__(self, *args, **kwargs):
        super(MockConnection, self).__init__(*args, **kwargs)
        self.host = mock.sentinel.host
        self.port = mock.sentinel.port
        self.response = []

    def queue_send(self, data):
        lines = (line for line in data.split('\n') if line)
        self.response.extend(lines)


class BaseTestCase(unittest.TestCase):
    def get_config(self):
        return {
            'mpd': {
                'password': None,
            }
        }

    def setUp(self):
        self.backend = dummy.create_dummy_backend_proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()

        self.connection = MockConnection()
        self.session = session.MpdSession(
            self.connection, config=self.get_config(), core=self.core)
        self.dispatcher = self.session.dispatcher
        self.context = self.dispatcher.context

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def sendRequest(self, request):
        self.connection.response = []
        request = '%s\n' % request.encode('utf-8')
        self.session.on_receive({'received': request})
        return self.connection.response

    def assertNoResponse(self):
        self.assertEqual([], self.connection.response)

    def assertInResponse(self, value):
        self.assertIn(
            value, self.connection.response,
            'Did not find %s in %s' % (
                repr(value), repr(self.connection.response)))

    def assertOnceInResponse(self, value):
        matched = len([r for r in self.connection.response if r == value])
        self.assertEqual(
            1, matched,
            'Expected to find %s once in %s' % (
                repr(value), repr(self.connection.response)))

    def assertNotInResponse(self, value):
        self.assertNotIn(
            value, self.connection.response,
            'Found %s in %s' % (
                repr(value), repr(self.connection.response)))

    def assertEqualResponse(self, value):
        self.assertEqual(1, len(self.connection.response))
        self.assertEqual(value, self.connection.response[0])
