from mopidy.models import Track

from tests.frontends.mpd import protocol


class StatusHandlerTest(protocol.BaseTestCase):
    def test_clearerror(self):
        self.sendRequest(u'clearerror')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_currentsong(self):
        track = Track()
        self.backend.current_playlist.append([track])
        self.backend.playback.play()
        self.sendRequest(u'currentsong')
        self.assertInResponse(u'file: ')
        self.assertInResponse(u'Time: 0')
        self.assertInResponse(u'Artist: ')
        self.assertInResponse(u'Title: ')
        self.assertInResponse(u'Album: ')
        self.assertInResponse(u'Track: 0')
        self.assertInResponse(u'Date: ')
        self.assertInResponse(u'Pos: 0')
        self.assertInResponse(u'Id: 0')
        self.assertInResponse(u'OK')

    def test_currentsong_without_song(self):
        self.sendRequest(u'currentsong')
        self.assertInResponse(u'OK')

    def test_stats_command(self):
        self.sendRequest(u'stats')
        self.assertInResponse(u'OK')

    def test_status_command(self):
        self.sendRequest(u'status')
        self.assertInResponse(u'OK')
