import unittest
import mock

from mopidy.backends import dummy as backend
from mopidy.frontends import mpd
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers import dummy as mixer
from mopidy.utils import network


class MockConnetion(mock.Mock):
    def __init__(self, *args, **kwargs):
        super(MockConnetion, self).__init__(*args, **kwargs)
        self.host = mock.sentinel.host
        self.port = mock.sentinel.port
        self.response = []

    def send(self, data):
        self.response.extend(data.split('\n'))


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.backend = backend.DummyBackend.start().proxy()
        self.mixer = mixer.DummyMixer.start().proxy()
        self.dispatcher = dispatcher.MpdDispatcher()

        self.connection = MockConnetion()
        self.session = mpd.MpdSession(self.connection)

    def tearDown(self):
        self.backend.stop().get()
        self.mixer.stop().get()

    def sendRequest(self, request, clear=False):
        self.connection.response = []
        self.session.on_line_received(request)

    def assertInResponse(self, value):
        self.assert_(value in self.connection.response, u'Did not find %s '
            'in %s' % (repr(value), repr(self.connection.response)))
