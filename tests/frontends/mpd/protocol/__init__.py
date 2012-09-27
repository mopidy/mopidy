import mock

from pykka.registry import ActorRegistry

from mopidy import core, settings
from mopidy.backends import dummy
from mopidy.frontends import mpd

from tests import unittest


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
    def setUp(self):
        self.backend = dummy.DummyBackend.start(audio=None).proxy()
        self.core = core.Core.start(backend=self.backend).proxy()

        self.connection = MockConnection()
        self.session = mpd.MpdSession(self.connection, core=self.core)
        self.dispatcher = self.session.dispatcher
        self.context = self.dispatcher.context

    def tearDown(self):
        ActorRegistry.stop_all()
        settings.runtime.clear()

    def sendRequest(self, request):
        self.connection.response = []
        request = '%s\n' % request.encode('utf-8')
        self.session.on_receive({'received': request})
        return self.connection.response

    def assertNoResponse(self):
        self.assertEqual([], self.connection.response)

    def assertInResponse(self, value):
        self.assertIn(value, self.connection.response, u'Did not find %s '
            'in %s' % (repr(value), repr(self.connection.response)))

    def assertOnceInResponse(self, value):
        matched = len([r for r in self.connection.response if r == value])
        self.assertEqual(1, matched, 'Expected to find %s once in %s' %
            (repr(value), repr(self.connection.response)))

    def assertNotInResponse(self, value):
        self.assertNotIn(value, self.connection.response, u'Found %s in %s' %
            (repr(value), repr(self.connection.response)))

    def assertEqualResponse(self, value):
        self.assertEqual(1, len(self.connection.response))
        self.assertEqual(value, self.connection.response[0])
