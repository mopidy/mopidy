from __future__ import unicode_literals

import mock
import unittest

import pykka

from mopidy.core import Core


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

    def test_backends_with_colliding_uri_schemes_fails(self):
        self.backend1.__class__.__name__ = b'B1'
        self.backend2.__class__.__name__ = b'B2'
        self.backend2.uri_schemes.get.return_value = ['dummy1', 'dummy2']
        self.assertRaisesRegexp(
            AssertionError,
            'Cannot add URI scheme dummy1 for B2, it is already handled by B1',
            Core, audio=None, backends=[self.backend1, self.backend2])
