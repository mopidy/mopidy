import datetime as dt
import unittest

from mopidy.frontends.mpd import translator, protocol
from mopidy.models import Album, Artist, Playlist, Track

class TrackMpdFormatTest(unittest.TestCase):
    def test_mpd_format_for_empty_track(self):
        result = translator.track_to_mpd_format(Track())
        self.assert_(('file', '') in result)
        self.assert_(('Time', 0) in result)
        self.assert_(('Artist', '') in result)
        self.assert_(('Title', '') in result)
        self.assert_(('Album', '') in result)
        self.assert_(('Track', 0) in result)
        self.assert_(('Date', '') in result)
        self.assertEqual(len(result), 7)

    def test_mpd_format_for_nonempty_track(self):
        track = Track(
            uri=u'a uri',
            artists=[Artist(name=u'an artist')],
            name=u'a name',
            album=Album(name=u'an album', num_tracks=13),
            track_no=7,
            date=dt.date(1977, 1, 1),
            length=137000,
        )
        result = translator.track_to_mpd_format(track, position=9, cpid=122)
        self.assert_(('file', 'a uri') in result)
        self.assert_(('Time', 137) in result)
        self.assert_(('Artist', 'an artist') in result)
        self.assert_(('Title', 'a name') in result)
        self.assert_(('Album', 'an album') in result)
        self.assert_(('Track', '7/13') in result)
        self.assert_(('Date', dt.date(1977, 1, 1)) in result)
        self.assert_(('Pos', 9) in result)
        self.assert_(('Id', 122) in result)
        self.assertEqual(len(result), 9)

    def test_mpd_format_artists(self):
        track = Track(artists=[Artist(name=u'ABBA'), Artist(name=u'Beatles')])
        translated = translator.track_artists_to_mpd_format(track)
        self.assertEqual(translated, u'ABBA, Beatles')


class PlaylistMpdFormatTest(unittest.TestCase):
    def test_mpd_format(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = translator.playlist_to_mpd_format(playlist)
        self.assertEqual(len(result), 3)

    def test_mpd_format_with_range(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = translator.playlist_to_mpd_format(playlist, 1, 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(dict(result[0])['Track'], 2)


class TracksToTagCacheFormatTest(unittest.TestCase):
    header_length = 4

    def check_headers(self, result):
        self.assert_(('info_begin',) in result)
        self.assert_(('mpd_version', protocol.VERSION) in result)
        self.assert_(('fs_charset', protocol.ENCODING) in result)
        self.assert_(('info_end',) in result)

    def test_empty_tag_cache(self):
        result = translator.tracks_to_tag_cache_format([])
        self.check_headers(result)

        self.assert_(('songList begin',) in result)
        self.assert_(('songList end',) in result)
        self.assertEqual(len(result), self.header_length+2)

