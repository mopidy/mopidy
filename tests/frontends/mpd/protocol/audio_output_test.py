from __future__ import unicode_literals

from tests.frontends.mpd import protocol


class AudioOutputHandlerTest(protocol.BaseTestCase):
    def test_enableoutput(self):
        self.sendRequest('enableoutput "0"')
        self.assertInResponse('OK')

    def test_disableoutput(self):
        self.sendRequest('disableoutput "0"')
        self.assertInResponse('OK')

    def test_outputs(self):
        self.sendRequest('outputs')
        self.assertInResponse('outputid: 0')
        self.assertInResponse('outputname: Default')
        self.assertInResponse('outputenabled: 1')
        self.assertInResponse('OK')
