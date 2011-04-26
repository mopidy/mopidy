import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer

class AudioOutputHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_enableoutput(self):
        result = self.h.handle_request(u'enableoutput "0"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_disableoutput(self):
        result = self.h.handle_request(u'disableoutput "0"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_outputs(self):
        result = self.h.handle_request(u'outputs')
        self.assert_(u'outputid: 0' in result)
        self.assert_(u'outputname: None' in result)
        self.assert_(u'outputenabled: 1' in result)
        self.assert_(u'OK' in result)
