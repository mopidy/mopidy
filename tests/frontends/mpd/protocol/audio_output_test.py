from __future__ import unicode_literals

from tests.frontends.mpd import protocol


class AudioOutputHandlerTest(protocol.BaseTestCase):
    def test_enableoutput(self):
        self.core.playback.mute = False

        self.sendRequest('enableoutput "0"')

        self.assertInResponse('OK')
        self.assertEqual(self.core.playback.mute.get(), True)

    def test_enableoutput_unknown_outputid(self):
        self.sendRequest('enableoutput "7"')

        self.assertInResponse('ACK [50@0] {enableoutput} No such audio output')

    def test_disableoutput(self):
        self.core.playback.mute = True

        self.sendRequest('disableoutput "0"')

        self.assertInResponse('OK')
        self.assertEqual(self.core.playback.mute.get(), False)

    def test_disableoutput_unknown_outputid(self):
        self.sendRequest('disableoutput "7"')

        self.assertInResponse(
            'ACK [50@0] {disableoutput} No such audio output')

    def test_outputs_when_unmuted(self):
        self.core.playback.mute = False

        self.sendRequest('outputs')

        self.assertInResponse('outputid: 0')
        self.assertInResponse('outputname: Mute')
        self.assertInResponse('outputenabled: 0')
        self.assertInResponse('OK')

    def test_outputs_when_muted(self):
        self.core.playback.mute = True

        self.sendRequest('outputs')

        self.assertInResponse('outputid: 0')
        self.assertInResponse('outputname: Mute')
        self.assertInResponse('outputenabled: 1')
        self.assertInResponse('OK')
