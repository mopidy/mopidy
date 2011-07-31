from tests.frontends.mpd import protocol


class AudioOutputHandlerTest(protocol.BaseTestCase):
    def test_enableoutput(self):
        self.sendRequest(u'enableoutput "0"')
        self.assertInResponse(u'ACK [0@0] {} Not implemented')

    def test_disableoutput(self):
        self.sendRequest(u'disableoutput "0"')
        self.assertInResponse(u'ACK [0@0] {} Not implemented')

    def test_outputs(self):
        self.sendRequest(u'outputs')
        self.assertInResponse(u'outputid: 0')
        self.assertInResponse(u'outputname: None')
        self.assertInResponse(u'outputenabled: 1')
        self.assertInResponse(u'OK')
