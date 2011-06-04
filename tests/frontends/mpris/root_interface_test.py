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

    def test_raise_does_nothing(self):
        self.mpris_object.Raise()

    def test_quit_should_stop_all_actors(self):
        self.mpris_object.Quit()
        self.assert_(mpris.ActorRegistry.stop_all.called)
