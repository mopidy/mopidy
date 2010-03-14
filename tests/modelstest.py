import datetime as dt
import unittest

from mopidy.models import Artist, Album, Track, Playlist

class ArtistTest(unittest.TestCase):
    def test_uri(self):
        uri = u'an_uri'
        artist = Artist(uri=uri)
        self.assertEqual(artist.uri, uri)
        self.assertRaises(AttributeError, setattr, artist, 'uri', None)

    def test_name(self):
        name = u'a name'
        artist = Artist(name=name)
        self.assertEqual(artist.name, name)
        self.assertRaises(AttributeError, setattr, artist, 'name', None)


class AlbumTest(unittest.TestCase):
    def test_uri(self):
        uri = u'an_uri'
        album = Album(uri=uri)
        self.assertEqual(album.uri, uri)
        self.assertRaises(AttributeError, setattr, album, 'uri', None)

    def test_name(self):
        name = u'a name'
        album = Album(name=name)
        self.assertEqual(album.name, name)
        self.assertRaises(AttributeError, setattr, album, 'name', None)

    def test_artists(self):
        artists = [Artist()]
        album = Album(artists=artists)
        self.assertEqual(album.artists, artists)
        self.assertRaises(AttributeError, setattr, album, 'artists', None)

    def test_num_tracks(self):
        num_tracks = 11
        album = Album(num_tracks=11)
        self.assertEqual(album.num_tracks, num_tracks)
        self.assertRaises(AttributeError, setattr, album, 'num_tracks', None)


class TrackTest(unittest.TestCase):
    def test_uri(self):
        uri = u'an_uri'
        track = Track(uri=uri)
        self.assertEqual(track.uri, uri)
        self.assertRaises(AttributeError, setattr, track, 'uri', None)

    def test_name(self):
        name = u'a name'
        track = Track(name=name)
        self.assertEqual(track.name, name)
        self.assertRaises(AttributeError, setattr, track, 'name', None)

    def test_artists(self):
        artists = [Artist(), Artist()]
        track = Track(artists=artists)
        self.assertEqual(track.artists, artists)
        self.assertRaises(AttributeError, setattr, track, 'artists', None)

    def test_album(self):
        album = Album()
        track = Track(album=album)
        self.assertEqual(track.album, album)
        self.assertRaises(AttributeError, setattr, track, 'album', None)

    def test_track_no(self):
        track_no = 7
        track = Track(track_no=track_no)
        self.assertEqual(track.track_no, track_no)
        self.assertRaises(AttributeError, setattr, track, 'track_no', None)

    def test_date(self):
        date = dt.date(1977, 1, 1)
        track = Track(date=date)
        self.assertEqual(track.date, date)
        self.assertRaises(AttributeError, setattr, track, 'date', None)

    def test_length(self):
        length = 137000
        track = Track(length=length)
        self.assertEqual(track.length, length)
        self.assertRaises(AttributeError, setattr, track, 'length', None)

    def test_bitrate(self):
        bitrate = 160
        track = Track(bitrate=bitrate)
        self.assertEqual(track.bitrate, bitrate)
        self.assertRaises(AttributeError, setattr, track, 'bitrate', None)

    def test_id(self):
        id = 17
        track = Track(id=id)
        self.assertEqual(track.id, id)
        self.assertRaises(AttributeError, setattr, track, 'id', None)

    def test_mpd_format_for_empty_track(self):
        track = Track()
        result = track.mpd_format()
        self.assert_(('file', '') in result)
        self.assert_(('Time', 0) in result)
        self.assert_(('Artist', '') in result)
        self.assert_(('Title', '') in result)
        self.assert_(('Album', '') in result)
        self.assert_(('Track', 0) in result)
        self.assert_(('Date', '') in result)
        self.assert_(('Pos', 0) in result)
        self.assert_(('Id', 0) in result)

    def test_mpd_format_for_nonempty_track(self):
        track = Track(
            uri=u'a uri',
            artists=[Artist(name=u'an artist')],
            name=u'a name',
            album=Album(name=u'an album', num_tracks=13),
            track_no=7,
            date=dt.date(1977, 1, 1),
            length=137000,
            id=122,
        )
        result = track.mpd_format(position=9)
        self.assert_(('file', 'a uri') in result)
        self.assert_(('Time', 137) in result)
        self.assert_(('Artist', 'an artist') in result)
        self.assert_(('Title', 'a name') in result)
        self.assert_(('Album', 'an album') in result)
        self.assert_(('Track', '7/13') in result)
        self.assert_(('Date', dt.date(1977, 1, 1)) in result)
        self.assert_(('Pos', 9) in result)
        self.assert_(('Id', 122) in result)

    def test_mpd_format_artists(self):
        track = Track(artists=[Artist(name=u'ABBA'), Artist(name=u'Beatles')])
        self.assertEqual(track.mpd_format_artists(), u'ABBA, Beatles')


class PlaylistTest(unittest.TestCase):
    def test_uri(self):
        uri = u'an_uri'
        playlist = Playlist(uri=uri)
        self.assertEqual(playlist.uri, uri)
        self.assertRaises(AttributeError, setattr, playlist, 'uri', None)

    def test_name(self):
        name = u'a name'
        playlist = Playlist(name=name)
        self.assertEqual(playlist.name, name)
        self.assertRaises(AttributeError, setattr, playlist, 'name', None)

    def test_tracks(self):
        tracks = [Track(), Track(), Track()]
        playlist = Playlist(tracks=tracks)
        self.assertEqual(playlist.tracks, tracks)
        self.assertRaises(AttributeError, setattr, playlist, 'tracks', None)

    def test_length(self):
        tracks = [Track(), Track(), Track()]
        playlist = Playlist(tracks=tracks)
        self.assertEqual(playlist.length, 3)

    def test_last_modified(self):
        last_modified = dt.datetime.now()
        playlist = Playlist(last_modified=last_modified)
        self.assertEqual(playlist.last_modified, last_modified)
        self.assertRaises(AttributeError, setattr, playlist, 'last_modified',
            None)

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
        self.assertEqual(dict(result[0])['Track'], 2)

    def test_mpd_format_with_negative_start_and_no_end(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = playlist.mpd_format(-1, None)
        self.assertEqual(len(result), 1)
        self.assertEqual(dict(result[0])['Track'], 3)

    def test_mpd_format_with_negative_start_and_end(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = playlist.mpd_format(-2, -1)
        self.assertEqual(len(result), 1)
        self.assertEqual(dict(result[0])['Track'], 2)

    def test_with_new_uri(self):
        tracks = [Track()]
        last_modified = dt.datetime.now()
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks,
            last_modified=last_modified)
        new_playlist = playlist.with_(uri=u'another uri')
        self.assertEqual(new_playlist.uri, u'another uri')
        self.assertEqual(new_playlist.name, u'a name')
        self.assertEqual(new_playlist.tracks, tracks)
        self.assertEqual(new_playlist.last_modified, last_modified)

    def test_with_new_name(self):
        tracks = [Track()]
        last_modified = dt.datetime.now()
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks,
            last_modified=last_modified)
        new_playlist = playlist.with_(name=u'another name')
        self.assertEqual(new_playlist.uri, u'an uri')
        self.assertEqual(new_playlist.name, u'another name')
        self.assertEqual(new_playlist.tracks, tracks)
        self.assertEqual(new_playlist.last_modified, last_modified)

    def test_with_new_tracks(self):
        tracks = [Track()]
        last_modified = dt.datetime.now()
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks,
            last_modified=last_modified)
        new_tracks = [Track(), Track()]
        new_playlist = playlist.with_(tracks=new_tracks)
        self.assertEqual(new_playlist.uri, u'an uri')
        self.assertEqual(new_playlist.name, u'a name')
        self.assertEqual(new_playlist.tracks, new_tracks)
        self.assertEqual(new_playlist.last_modified, last_modified)

    def test_with_new_last_modified(self):
        tracks = [Track()]
        last_modified = dt.datetime.now()
        new_last_modified = last_modified + dt.timedelta(1)
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks,
            last_modified=last_modified)
        new_playlist = playlist.with_(last_modified=new_last_modified)
        self.assertEqual(new_playlist.uri, u'an uri')
        self.assertEqual(new_playlist.name, u'a name')
        self.assertEqual(new_playlist.tracks, tracks)
        self.assertEqual(new_playlist.last_modified, new_last_modified)
