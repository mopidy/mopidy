import mock
import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpris import objects

class RootInterfaceTest(unittest.TestCase):
    def setUp(self):
        objects.exit_process = mock.Mock()
        objects.MprisObject._connect_to_dbus = mock.Mock()
        self.backend = DummyBackend.start().proxy()
        self.mpris = objects.MprisObject()

    def tearDown(self):
        self.backend.stop()

    def test_constructor_connects_to_dbus(self):
        self.assert_(self.mpris._connect_to_dbus.called)

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

    def test_supported_uri_schemes_is_empty(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'SupportedUriSchemes')
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0], 'dummy')

    def test_supported_mime_types_is_empty(self):
        result = self.mpris.Get(objects.ROOT_IFACE, 'SupportedMimeTypes')
        self.assertEquals(len(result), 0)
