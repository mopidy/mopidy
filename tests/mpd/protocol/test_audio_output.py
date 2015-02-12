from __future__ import absolute_import, unicode_literals

from tests.mpd import protocol


class AudioOutputHandlerTest(protocol.BaseTestCase):
    def test_enableoutput(self):
        self.core.mixer.set_mute(False)

        self.send_request('enableoutput "0"')

        self.assertInResponse('OK')
        self.assertEqual(self.core.mixer.get_mute().get(), True)

    def test_enableoutput_unknown_outputid(self):
        self.send_request('enableoutput "7"')

        self.assertInResponse('ACK [50@0] {enableoutput} No such audio output')

    def test_disableoutput(self):
        self.core.mixer.set_mute(True)

        self.send_request('disableoutput "0"')

        self.assertInResponse('OK')
        self.assertEqual(self.core.mixer.get_mute().get(), False)

    def test_disableoutput_unknown_outputid(self):
        self.send_request('disableoutput "7"')

        self.assertInResponse(
            'ACK [50@0] {disableoutput} No such audio output')

    def test_outputs_when_unmuted(self):
        self.core.mixer.set_mute(False)

        self.send_request('outputs')

        self.assertInResponse('outputid: 0')
        self.assertInResponse('outputname: Mute')
        self.assertInResponse('outputenabled: 0')
        self.assertInResponse('OK')

    def test_outputs_when_muted(self):
        self.core.mixer.set_mute(True)

        self.send_request('outputs')

        self.assertInResponse('outputid: 0')
        self.assertInResponse('outputname: Mute')
        self.assertInResponse('outputenabled: 1')
        self.assertInResponse('OK')
