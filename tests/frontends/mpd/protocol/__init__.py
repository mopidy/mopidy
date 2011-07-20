import unittest
import mock

from mopidy import settings
from mopidy.backends import dummy as backend
from mopidy.frontends import mpd
from mopidy.mixers import dummy as mixer


class MockConnetion(mock.Mock):
    def __init__(self, *args, **kwargs):
        super(MockConnetion, self).__init__(*args, **kwargs)
        self.host = mock.sentinel.host
        self.port = mock.sentinel.port
        self.response = []

    def send(self, data):
        lines = (line for line in data.split('\n') if line)
        self.response.extend(lines)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.backend = backend.DummyBackend.start().proxy()
        self.mixer = mixer.DummyMixer.start().proxy()

        self.connection = MockConnetion()
        self.session = mpd.MpdSession(self.connection)
        self.dispatcher = self.session.dispatcher

    def tearDown(self):
        self.backend.stop().get()
        self.mixer.stop().get()
        settings.runtime.clear()

    def sendRequest(self, request, clear=False):
        self.connection.response = []
        self.session.on_line_received(request)
        return self.connection.response

    def assertInResponse(self, value):
        self.assert_(value in self.connection.response, u'Did not find %s '
            'in %s' % (repr(value), repr(self.connection.response)))

    def assertNotInResponse(self, value):
        self.assert_(value not in self.connection.response, u'Found %s in %s' %
            (repr(value), repr(self.connection.response)))

    def assertEqualResponse(self, value):
        self.assertEqual(1, len(self.connection.response))
        self.assertEqual(value, self.connection.response[0])
