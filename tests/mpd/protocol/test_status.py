from __future__ import absolute_import, unicode_literals

from mopidy.models import Track

from tests.mpd import protocol


class StatusHandlerTest(protocol.BaseTestCase):
    def test_clearerror(self):
        self.send_request('clearerror')
        self.assertEqualResponse('ACK [0@0] {clearerror} Not implemented')

    def test_currentsong(self):
        track = Track()
        self.core.tracklist.add([track])
        self.core.playback.play()
        self.send_request('currentsong')
        self.assertInResponse('file: ')
        self.assertInResponse('Time: 0')
        self.assertInResponse('Artist: ')
        self.assertInResponse('Title: ')
        self.assertInResponse('Album: ')
        self.assertInResponse('Track: 0')
        self.assertNotInResponse('Date: ')
        self.assertInResponse('Pos: 0')
        self.assertInResponse('Id: 0')
        self.assertInResponse('OK')

    def test_currentsong_without_song(self):
        self.send_request('currentsong')
        self.assertInResponse('OK')

    def test_stats_command(self):
        self.send_request('stats')
        self.assertInResponse('OK')

    def test_status_command(self):
        self.send_request('status')
        self.assertInResponse('OK')
