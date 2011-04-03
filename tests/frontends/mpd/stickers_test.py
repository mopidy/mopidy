import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer

class StickersHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_sticker_get(self):
        result = self.h.handle_request(
            u'sticker get "song" "file:///dev/urandom" "a_name"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_sticker_set(self):
        result = self.h.handle_request(
            u'sticker set "song" "file:///dev/urandom" "a_name" "a_value"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_sticker_delete_with_name(self):
        result = self.h.handle_request(
            u'sticker delete "song" "file:///dev/urandom" "a_name"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_sticker_delete_without_name(self):
        result = self.h.handle_request(
            u'sticker delete "song" "file:///dev/urandom"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_sticker_list(self):
        result = self.h.handle_request(
            u'sticker list "song" "file:///dev/urandom"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_sticker_find(self):
        result = self.h.handle_request(
            u'sticker find "song" "file:///dev/urandom" "a_name"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)
