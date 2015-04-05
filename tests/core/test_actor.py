from __future__ import absolute_import, unicode_literals

import unittest

import mock

import pykka

from mopidy.core import Core
from mopidy.utils import versioning


class CoreActorTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.backend1.actor_ref.actor_class.__name__ = b'B1'

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']
        self.backend2.actor_ref.actor_class.__name__ = b'B2'

        self.core = Core(mixer=None, backends=[self.backend1, self.backend2])

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def test_uri_schemes_has_uris_from_all_backends(self):
        result = self.core.uri_schemes

        self.assertIn('dummy1', result)
        self.assertIn('dummy2', result)

    def test_backends_with_colliding_uri_schemes_fails(self):
        self.backend2.uri_schemes.get.return_value = ['dummy1', 'dummy2']

        self.assertRaisesRegexp(
            AssertionError,
            'Cannot add URI scheme dummy1 for B2, it is already handled by B1',
            Core, mixer=None, backends=[self.backend1, self.backend2])

    def test_version(self):
        self.assertEqual(self.core.version, versioning.get_version())
