import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.mixers.dummy import DummyMixer

class AudioOutputHandlerTest(unittest.TestCase):
    def setUp(self):
        self.backend = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.dispatcher = MpdDispatcher()

    def tearDown(self):
        self.backend.stop().get()
        self.mixer.stop().get()

    def test_enableoutput(self):
        result = self.dispatcher.handle_request(u'enableoutput "0"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_disableoutput(self):
        result = self.dispatcher.handle_request(u'disableoutput "0"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_outputs(self):
        result = self.dispatcher.handle_request(u'outputs')
        self.assert_(u'outputid: 0' in result)
        self.assert_(u'outputname: None' in result)
        self.assert_(u'outputenabled: 1' in result)
        self.assert_(u'OK' in result)
