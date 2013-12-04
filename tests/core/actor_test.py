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
        self.backend1.actor_ref.actor_class.__name__ = b'B1'
        self.backend2.actor_ref.actor_class.__name__ = b'B2'
        self.backend2.uri_schemes.get.return_value = ['dummy1', 'dummy2']
        self.assertRaisesRegexp(
            AssertionError,
            'Cannot add URI scheme dummy1 for B2, it is already handled by B1',
            Core, audio=None, backends=[self.backend1, self.backend2])

    def test_backends_with_colliding_uri_schemes_passes(self):
        """
        Checks that backends with overlapping schemes, but distinct sub parts
        provided can co-exist.
        """

        self.backend1.has_library().get.return_value = False
        self.backend1.has_playlists().get.return_value = False

        self.backend2.uri_schemes.get.return_value = ['dummy1']
        self.backend2.has_playback().get.return_value = False
        self.backend2.has_playlists().get.return_value = False

        core = Core(audio=None, backends=[self.backend1, self.backend2])
        self.assertEqual(core.backends.with_playback,
                         {'dummy1': self.backend1})
        self.assertEqual(core.backends.with_library,
                         {'dummy1': self.backend2})
