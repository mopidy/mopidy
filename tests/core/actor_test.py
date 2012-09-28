import mock
import pykka

from mopidy.core import Core

from tests import unittest


class CoreActorTest(unittest.TestCase):
    def setUp(self):
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']

        self.core = Core(audio=None, backends=[self.backend1, self.backend2])

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_uri_schemes_has_uris_from_all_backends(self):
        result = self.core.uri_schemes

        self.assertIn('dummy1', result)
        self.assertIn('dummy2', result)
