from __future__ import unicode_literals

import sys

import mock
import pykka

from mopidy import core, exceptions, settings
from mopidy.backends import dummy

try:
    from mopidy.frontends.mpris import objects
except exceptions.OptionalDependencyError:
    pass

from tests import unittest


@unittest.skipUnless(sys.platform.startswith('linux'), 'requires Linux')
class RootInterfaceTest(unittest.TestCase):
    def setUp(self):
        objects.exit_process = mock.Mock()
        objects.MprisObject._connect_to_dbus = mock.Mock()
        self.backend = dummy.DummyBackend.start(audio=None).proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()
        self.mpris = objects.MprisObject(core=self.core)

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_constructor_connects_to_dbus(self):
        self.assert_(self.mpris._connect_to_dbus.called)

    def test_fullscreen_returns_false(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'Fullscreen')
        self.assertFalse(result)

    def test_setting_fullscreen_fails_and_returns_none(self):
        result = self.mpris.Set(objects.ROOT_IFACE, 'Fullscreen', 'True')
        self.assertIsNone(result)

    def test_can_set_fullscreen_returns_false(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'CanSetFullscreen')
        self.assertFalse(result)

    def test_can_raise_returns_false(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'CanRaise')
        self.assertFalse(result)

    def test_raise_does_nothing(self):
        self.mpris.Raise()

    def test_can_quit_returns_true(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'CanQuit')
        self.assertTrue(result)

    def test_quit_should_stop_all_actors(self):
        self.mpris.Quit()
        self.assert_(objects.exit_process.called)

    def test_has_track_list_returns_false(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'HasTrackList')
        self.assertFalse(result)

    def test_identify_is_mopidy(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'Identity')
        self.assertEquals(result, 'Mopidy')

    def test_desktop_entry_is_mopidy(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'DesktopEntry')
        self.assertEquals(result, 'mopidy')

    def test_desktop_entry_is_based_on_DESKTOP_FILE_setting(self):
        settings.runtime['DESKTOP_FILE'] = '/tmp/foo.desktop'
        result = self.mpris.Get(objects.ROOT_IFACE, 'DesktopEntry')
        self.assertEquals(result, 'foo')
        settings.runtime.clear()

    def test_supported_uri_schemes_includes_backend_uri_schemes(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'SupportedUriSchemes')
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0], 'dummy')

    def test_supported_mime_types_is_empty(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'SupportedMimeTypes')
        self.assertEquals(len(result), 0)
