import datetime as dt
import unittest

from mopidy.models import Artist, Album, Track, Playlist

class ArtistTest(unittest.TestCase):
    def test_uri(self):
        uri = u'an_uri'
        artist = Artist(uri=uri)
        self.assertEqual(artist.uri, uri)

    def test_name(self):
        name = u'a name'
        artist = Artist(name=name)
        self.assertEqual(artist.name, name)


class AlbumTest(unittest.TestCase):
    def test_uri(self):
        uri = u'an_uri'
        album = Album(uri=uri)
        self.assertEqual(album.uri, uri)

    def test_name(self):
        name = u'a name'
        album = Album(name=name)
        self.assertEqual(album.name, name)

    def test_artists(self):
        artists = [Artist()]
        album = Album(artists=artists)
        self.assertEqual(album.artists, artists)

    def test_num_tracks(self):
        num_tracks = 11
        album = Album(num_tracks=11)
        self.assertEqual(album.num_tracks, num_tracks)


class TrackTest(unittest.TestCase):
    def test_uri(self):
        uri = u'an_uri'
        track = Track(uri=uri)
        self.assertEqual(track.uri, uri)

    def test_title(self):
        title = u'a title'
        track = Track(title=title)
        self.assertEqual(track.title, title)

    def test_artists(self):
        artists = [Artist(), Artist()]
        track = Track(artists=artists)
        self.assertEqual(track.artists, artists)

    def test_album(self):
        album = Album()
        track = Track(album=album)
        self.assertEqual(track.album, album)

    def test_track_no(self):
        track_no = 7
        track = Track(track_no=track_no)
        self.assertEqual(track.track_no, track_no)

    def test_date(self):
        date = dt.date(1977, 1, 1)
        track = Track(date=date)
        self.assertEqual(track.date, date)

    def test_length(self):
        length = 137000
        track = Track(length=length)
        self.assertEqual(track.length, length)

    def test_bitrate(self):
        bitrate = 160
        track = Track(bitrate=bitrate)
        self.assertEqual(track.bitrate, bitrate)

    def test_id(self):
        id = 17
        track = Track(id=id)
        self.assertEqual(track.id, id)

    def test_mpd_format_for_empty_track(self):
        track = Track()
        result = track.mpd_format()
        self.assert_(('file', '') in result)
        self.assert_(('Time', 0) in result)
        self.assert_(('Artist', '') in result)
        self.assert_(('Title', '') in result)
        self.assert_(('Album', '') in result)
        self.assert_(('Track', '0/0') in result)
        self.assert_(('Date', '') in result)
        self.assert_(('Pos', 0) in result)
        self.assert_(('Id', 0) in result)

    def test_mpd_format_artists(self):
        track = Track(artists=[Artist(name=u'ABBA'), Artist(name=u'Beatles')])
        self.assertEqual(track.mpd_format_artists(), u'ABBA, Beatles')

class PlaylistTest(unittest.TestCase):
    def test_uri(self):
        uri = u'an_uri'
        playlist = Playlist(uri=uri)
        self.assertEqual(playlist.uri, uri)

    def test_name(self):
        name = u'a name'
        playlist = Playlist(name=name)
        self.assertEqual(playlist.name, name)

    def test_tracks(self):
        tracks = [Track(), Track(), Track()]
        playlist = Playlist(tracks=tracks)
        self.assertEqual(playlist.tracks, tracks)

    def test_length(self):
        tracks = [Track(), Track(), Track()]
        playlist = Playlist(tracks=tracks)
        self.assertEqual(playlist.length, 3)

    def test_mpd_format(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = playlist.mpd_format()
        self.assertEqual(len(result), 3)

    def test_mpd_format_with_range(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = playlist.mpd_format(1, 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(dict(result[0])['Track'], '2/0')

    def test_with_new_uri(self):
        tracks = [Track()]
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks)
        new_playlist = playlist.with_(uri=u'another uri')
        self.assertEqual(new_playlist.uri, u'another uri')
        self.assertEqual(new_playlist.name, u'a name')
        self.assertEqual(new_playlist.tracks, tracks)

    def test_with_new_name(self):
        tracks = [Track()]
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks)
        new_playlist = playlist.with_(name=u'another name')
        self.assertEqual(new_playlist.uri, u'an uri')
        self.assertEqual(new_playlist.name, u'another name')
        self.assertEqual(new_playlist.tracks, tracks)

    def test_with_new_tracks(self):
        tracks = [Track()]
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks)
        new_tracks = [Track(), Track()]
        new_playlist = playlist.with_(tracks=new_tracks)
        self.assertEqual(new_playlist.uri, u'an uri')
        self.assertEqual(new_playlist.name, u'a name')
        self.assertEqual(new_playlist.tracks, new_tracks)
