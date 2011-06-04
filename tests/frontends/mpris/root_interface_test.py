import mock
import unittest

from pykka.registry import ActorRegistry

from mopidy.frontends import mpris

class RootInterfaceTest(unittest.TestCase):
    def setUp(self):
        mpris.ActorRegistry = mock.Mock(spec=ActorRegistry)
        mpris.MprisObject._connect_to_dbus = mock.Mock()
        self.mpris_object = mpris.MprisObject()

    def test_constructor_connects_to_dbus(self):
        self.assert_(self.mpris_object._connect_to_dbus.called)

    def test_can_raise_returns_false(self):
        result = self.mpris_object.Get(mpris.ROOT_IFACE, 'CanRaise')
        self.assertFalse(result)

    def test_raise_does_nothing(self):
        self.mpris_object.Raise()

    def test_can_quit_returns_true(self):
        result = self.mpris_object.Get(mpris.ROOT_IFACE, 'CanQuit')
        self.assertTrue(result)

    def test_quit_should_stop_all_actors(self):
        self.mpris_object.Quit()
        self.assert_(mpris.ActorRegistry.stop_all.called)

    def test_has_track_list_returns_false(self):
        result = self.mpris_object.Get(mpris.ROOT_IFACE, 'HasTrackList')
        self.assertFalse(result)

    def test_identify_is_mopidy(self):
        result = self.mpris_object.Get(mpris.ROOT_IFACE, 'Identity')
        self.assertEquals('Mopidy', result)

    def test_supported_uri_schemes_is_empty(self):
        result = self.mpris_object.Get(mpris.ROOT_IFACE, 'SupportedUriSchemes')
        self.assertEquals(0, len(result))

    def test_supported_mime_types_is_empty(self):
        result = self.mpris_object.Get(mpris.ROOT_IFACE, 'SupportedMimeTypes')
        self.assertEquals(0, len(result))
