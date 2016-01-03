from __future__ import absolute_import, unicode_literals

import shutil
import tempfile
import unittest

import mock

import pykka

from mopidy.core import Core
from mopidy.internal import versioning


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
            'Cannot add URI scheme "dummy1" for B2, '
            'it is already handled by B1',
            Core, mixer=None, backends=[self.backend1, self.backend2])

    def test_version(self):
        self.assertEqual(self.core.version, versioning.get_version())


class CoreActorExportRestoreTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        config = {
            'core': {
                'max_tracklist_length': 10000,
                'restore_state': 'play',
                'data_dir': self.temp_dir,
            }
        }

        self.core = Core.start(
            config=config, mixer=None, backends=[]).proxy()

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()
        shutil.rmtree(self.temp_dir)

    def test_restore_on_start(self):
        # cover mopidy.core.actor.on_start and .on_stop
        # starting the actor by calling any function:
        self.core.get_version()
        pass
