import datetime

from mopidy.models import Artist, Album, CpTrack, Track, Playlist

from tests import unittest


class GenericCopyTets(unittest.TestCase):
    def compare(self, orig, other):
        self.assertEqual(orig, other)
        self.assertNotEqual(id(orig), id(other))

    def test_copying_track(self):
        track = Track()
        self.compare(track, track.copy())

    def test_copying_artist(self):
        artist = Artist()
        self.compare(artist, artist.copy())

    def test_copying_album(self):
        album = Album()
        self.compare(album, album.copy())

    def test_copying_playlist(self):
        playlist = Playlist()
        self.compare(playlist, playlist.copy())

    def test_copying_track_with_basic_values(self):
        track = Track(name='foo', uri='bar')
        copy = track.copy(name='baz')
        self.assertEqual('baz', copy.name)
        self.assertEqual('bar', copy.uri)

    def test_copying_track_with_missing_values(self):
        track = Track(uri='bar')
        copy = track.copy(name='baz')
        self.assertEqual('baz', copy.name)
        self.assertEqual('bar', copy.uri)

    def test_copying_track_with_private_internal_value(self):
        artist1 = Artist(name='foo')
        artist2 = Artist(name='bar')
        track = Track(artists=[artist1])
        copy = track.copy(artists=[artist2])
        self.assert_(artist2 in copy.artists)

    def test_copying_track_with_invalid_key(self):
        test = lambda: Track().copy(invalid_key=True)
        self.assertRaises(TypeError, test)


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

    def test_musicbrainz_id(self):
        mb_id = u'mb-id'
        artist = Artist(musicbrainz_id=mb_id)
        self.assertEqual(artist.musicbrainz_id, mb_id)
        self.assertRaises(AttributeError, setattr, artist,
            'musicbrainz_id', None)

    def test_invalid_kwarg(self):
        test = lambda: Artist(foo='baz')
        self.assertRaises(TypeError, test)

    def test_repr(self):
        self.assertEquals(
            "Artist(name='name', uri='uri')",
            repr(Artist(uri='uri', name='name')))

    def test_eq_name(self):
        artist1 = Artist(name=u'name')
        artist2 = Artist(name=u'name')
        self.assertEqual(artist1, artist2)
        self.assertEqual(hash(artist1), hash(artist2))

    def test_eq_uri(self):
        artist1 = Artist(uri=u'uri')
        artist2 = Artist(uri=u'uri')
        self.assertEqual(artist1, artist2)
        self.assertEqual(hash(artist1), hash(artist2))

    def test_eq_musibrainz_id(self):
        artist1 = Artist(musicbrainz_id=u'id')
        artist2 = Artist(musicbrainz_id=u'id')
        self.assertEqual(artist1, artist2)
        self.assertEqual(hash(artist1), hash(artist2))

    def test_eq(self):
        artist1 = Artist(uri=u'uri', name=u'name', musicbrainz_id='id')
        artist2 = Artist(uri=u'uri', name=u'name', musicbrainz_id='id')
        self.assertEqual(artist1, artist2)
        self.assertEqual(hash(artist1), hash(artist2))

    def test_eq_none(self):
        self.assertNotEqual(Artist(), None)

    def test_eq_other(self):
        self.assertNotEqual(Artist(), 'other')

    def test_ne_name(self):
        artist1 = Artist(name=u'name1')
        artist2 = Artist(name=u'name2')
        self.assertNotEqual(artist1, artist2)
        self.assertNotEqual(hash(artist1), hash(artist2))

    def test_ne_uri(self):
        artist1 = Artist(uri=u'uri1')
        artist2 = Artist(uri=u'uri2')
        self.assertNotEqual(artist1, artist2)
        self.assertNotEqual(hash(artist1), hash(artist2))

    def test_ne_musicbrainz_id(self):
        artist1 = Artist(musicbrainz_id=u'id1')
        artist2 = Artist(musicbrainz_id=u'id2')
        self.assertNotEqual(artist1, artist2)
        self.assertNotEqual(hash(artist1), hash(artist2))

    def test_ne(self):
        artist1 = Artist(uri=u'uri1', name=u'name1', musicbrainz_id='id1')
        artist2 = Artist(uri=u'uri2', name=u'name2', musicbrainz_id='id2')
        self.assertNotEqual(artist1, artist2)
        self.assertNotEqual(hash(artist1), hash(artist2))


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
        artist = Artist()
        album = Album(artists=[artist])
        self.assert_(artist in album.artists)
        self.assertRaises(AttributeError, setattr, album, 'artists', None)

    def test_num_tracks(self):
        num_tracks = 11
        album = Album(num_tracks=11)
        self.assertEqual(album.num_tracks, num_tracks)
        self.assertRaises(AttributeError, setattr, album, 'num_tracks', None)

    def test_musicbrainz_id(self):
        mb_id = u'mb-id'
        album = Album(musicbrainz_id=mb_id)
        self.assertEqual(album.musicbrainz_id, mb_id)
        self.assertRaises(AttributeError, setattr, album,
            'musicbrainz_id', None)

    def test_invalid_kwarg(self):
        test = lambda: Album(foo='baz')
        self.assertRaises(TypeError, test)

    def test_repr_without_artists(self):
        self.assertEquals(
            "Album(artists=[], name='name', uri='uri')",
            repr(Album(uri='uri', name='name')))

    def test_repr_with_artists(self):
        self.assertEquals(
            "Album(artists=[Artist(name='foo')], name='name', uri='uri')",
            repr(Album(uri='uri', name='name', artists=[Artist(name='foo')])))

    def test_eq_name(self):
        album1 = Album(name=u'name')
        album2 = Album(name=u'name')
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_uri(self):
        album1 = Album(uri=u'uri')
        album2 = Album(uri=u'uri')
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_artists(self):
        artists = [Artist()]
        album1 = Album(artists=artists)
        album2 = Album(artists=artists)
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_artists_order(self):
        artist1 = Artist(name=u'name1')
        artist2 = Artist(name=u'name2')
        album1 = Album(artists=[artist1, artist2])
        album2 = Album(artists=[artist2, artist1])
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_num_tracks(self):
        album1 = Album(num_tracks=2)
        album2 = Album(num_tracks=2)
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_musibrainz_id(self):
        album1 = Album(musicbrainz_id=u'id')
        album2 = Album(musicbrainz_id=u'id')
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq(self):
        artists = [Artist()]
        album1 = Album(name=u'name', uri=u'uri', artists=artists, num_tracks=2,
            musicbrainz_id='id')
        album2 = Album(name=u'name', uri=u'uri', artists=artists, num_tracks=2,
            musicbrainz_id='id')
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_none(self):
        self.assertNotEqual(Album(), None)

    def test_eq_other(self):
        self.assertNotEqual(Album(), 'other')

    def test_ne_name(self):
        album1 = Album(name=u'name1')
        album2 = Album(name=u'name2')
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne_uri(self):
        album1 = Album(uri=u'uri1')
        album2 = Album(uri=u'uri2')
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne_artists(self):
        album1 = Album(artists=[Artist(name=u'name1')])
        album2 = Album(artists=[Artist(name=u'name2')])
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne_num_tracks(self):
        album1 = Album(num_tracks=1)
        album2 = Album(num_tracks=2)
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne_musicbrainz_id(self):
        album1 = Album(musicbrainz_id=u'id1')
        album2 = Album(musicbrainz_id=u'id2')
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne(self):
        album1 = Album(name=u'name1', uri=u'uri1',
            artists=[Artist(name=u'name1')], num_tracks=1,
            musicbrainz_id='id1')
        album2 = Album(name=u'name2', uri=u'uri2',
            artists=[Artist(name=u'name2')], num_tracks=2,
            musicbrainz_id='id2')
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))


class CpTrackTest(unittest.TestCase):
    def setUp(self):
        self.cpid = 123
        self.track = Track()
        self.cp_track = CpTrack(self.cpid, self.track)

    def test_cp_track_can_be_accessed_as_a_tuple(self):
        self.assertEqual(self.cpid, self.cp_track[0])
        self.assertEqual(self.track, self.cp_track[1])

    def test_cp_track_can_be_accessed_by_attribute_names(self):
        self.assertEqual(self.cpid, self.cp_track.cpid)
        self.assertEqual(self.track, self.cp_track.track)


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
        artists = [Artist(name=u'name1'), Artist(name=u'name2')]
        track = Track(artists=artists)
        self.assertEqual(set(track.artists), set(artists))
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
        date = datetime.date(1977, 1, 1)
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

    def test_musicbrainz_id(self):
        mb_id = u'mb-id'
        track = Track(musicbrainz_id=mb_id)
        self.assertEqual(track.musicbrainz_id, mb_id)
        self.assertRaises(AttributeError, setattr, track,
            'musicbrainz_id', None)

    def test_invalid_kwarg(self):
        test = lambda: Track(foo='baz')
        self.assertRaises(TypeError, test)

    def test_repr_without_artists(self):
        self.assertEquals(
            "Track(artists=[], name='name', uri='uri')",
            repr(Track(uri='uri', name='name')))

    def test_repr_with_artists(self):
        self.assertEquals(
            "Track(artists=[Artist(name='foo')], name='name', uri='uri')",
            repr(Track(uri='uri', name='name', artists=[Artist(name='foo')])))

    def test_eq_uri(self):
        track1 = Track(uri=u'uri1')
        track2 = Track(uri=u'uri1')
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_name(self):
        track1 = Track(name=u'name1')
        track2 = Track(name=u'name1')
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_artists(self):
        artists = [Artist()]
        track1 = Track(artists=artists)
        track2 = Track(artists=artists)
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_artists_order(self):
        artist1 = Artist(name=u'name1')
        artist2 = Artist(name=u'name2')
        track1 = Track(artists=[artist1, artist2])
        track2 = Track(artists=[artist2, artist1])
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_album(self):
        album = Album()
        track1 = Track(album=album)
        track2 = Track(album=album)
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_track_no(self):
        track1 = Track(track_no=1)
        track2 = Track(track_no=1)
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_date(self):
        date = datetime.date.today()
        track1 = Track(date=date)
        track2 = Track(date=date)
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_length(self):
        track1 = Track(length=100)
        track2 = Track(length=100)
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_bitrate(self):
        track1 = Track(bitrate=100)
        track2 = Track(bitrate=100)
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_musibrainz_id(self):
        track1 = Track(musicbrainz_id=u'id')
        track2 = Track(musicbrainz_id=u'id')
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq(self):
        date = datetime.date.today()
        artists = [Artist()]
        album = Album()
        track1 = Track(uri=u'uri', name=u'name', artists=artists, album=album,
            track_no=1, date=date, length=100, bitrate=100,
            musicbrainz_id='id')
        track2 = Track(uri=u'uri', name=u'name', artists=artists, album=album,
            track_no=1, date=date, length=100, bitrate=100,
            musicbrainz_id='id')
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_none(self):
        self.assertNotEqual(Track(), None)

    def test_eq_other(self):
        self.assertNotEqual(Track(), 'other')

    def test_ne_uri(self):
        track1 = Track(uri=u'uri1')
        track2 = Track(uri=u'uri2')
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_name(self):
        track1 = Track(name=u'name1')
        track2 = Track(name=u'name2')
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_artists(self):
        track1 = Track(artists=[Artist(name=u'name1')])
        track2 = Track(artists=[Artist(name=u'name2')])
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_album(self):
        track1 = Track(album=Album(name=u'name1'))
        track2 = Track(album=Album(name=u'name2'))
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_track_no(self):
        track1 = Track(track_no=1)
        track2 = Track(track_no=2)
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_date(self):
        track1 = Track(date=datetime.date.today())
        track2 = Track(date=datetime.date.today()-datetime.timedelta(days=1))
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_length(self):
        track1 = Track(length=100)
        track2 = Track(length=200)
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_bitrate(self):
        track1 = Track(bitrate=100)
        track2 = Track(bitrate=200)
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_musicbrainz_id(self):
        track1 = Track(musicbrainz_id=u'id1')
        track2 = Track(musicbrainz_id=u'id2')
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne(self):
        track1 = Track(uri=u'uri1', name=u'name1',
            artists=[Artist(name=u'name1')], album=Album(name=u'name1'),
            track_no=1, date=datetime.date.today(), length=100, bitrate=100,
            musicbrainz_id='id1')
        track2 = Track(uri=u'uri2', name=u'name2',
            artists=[Artist(name=u'name2')], album=Album(name=u'name2'),
            track_no=2, date=datetime.date.today()-datetime.timedelta(days=1),
            length=200, bitrate=200, musicbrainz_id='id2')
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))


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
        self.assertEqual(list(playlist.tracks), tracks)
        self.assertRaises(AttributeError, setattr, playlist, 'tracks', None)

    def test_length(self):
        tracks = [Track(), Track(), Track()]
        playlist = Playlist(tracks=tracks)
        self.assertEqual(playlist.length, 3)

    def test_last_modified(self):
        last_modified = datetime.datetime.now()
        playlist = Playlist(last_modified=last_modified)
        self.assertEqual(playlist.last_modified, last_modified)
        self.assertRaises(AttributeError, setattr, playlist, 'last_modified',
            None)

    def test_with_new_uri(self):
        tracks = [Track()]
        last_modified = datetime.datetime.now()
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks,
            last_modified=last_modified)
        new_playlist = playlist.copy(uri=u'another uri')
        self.assertEqual(new_playlist.uri, u'another uri')
        self.assertEqual(new_playlist.name, u'a name')
        self.assertEqual(list(new_playlist.tracks), tracks)
        self.assertEqual(new_playlist.last_modified, last_modified)

    def test_with_new_name(self):
        tracks = [Track()]
        last_modified = datetime.datetime.now()
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks,
            last_modified=last_modified)
        new_playlist = playlist.copy(name=u'another name')
        self.assertEqual(new_playlist.uri, u'an uri')
        self.assertEqual(new_playlist.name, u'another name')
        self.assertEqual(list(new_playlist.tracks), tracks)
        self.assertEqual(new_playlist.last_modified, last_modified)

    def test_with_new_tracks(self):
        tracks = [Track()]
        last_modified = datetime.datetime.now()
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks,
            last_modified=last_modified)
        new_tracks = [Track(), Track()]
        new_playlist = playlist.copy(tracks=new_tracks)
        self.assertEqual(new_playlist.uri, u'an uri')
        self.assertEqual(new_playlist.name, u'a name')
        self.assertEqual(list(new_playlist.tracks), new_tracks)
        self.assertEqual(new_playlist.last_modified, last_modified)

    def test_with_new_last_modified(self):
        tracks = [Track()]
        last_modified = datetime.datetime.now()
        new_last_modified = last_modified + datetime.timedelta(1)
        playlist = Playlist(uri=u'an uri', name=u'a name', tracks=tracks,
            last_modified=last_modified)
        new_playlist = playlist.copy(last_modified=new_last_modified)
        self.assertEqual(new_playlist.uri, u'an uri')
        self.assertEqual(new_playlist.name, u'a name')
        self.assertEqual(list(new_playlist.tracks), tracks)
        self.assertEqual(new_playlist.last_modified, new_last_modified)

    def test_invalid_kwarg(self):
        test = lambda: Playlist(foo='baz')
        self.assertRaises(TypeError, test)

    def test_repr_without_tracks(self):
        self.assertEquals(
            "Playlist(name='name', tracks=[], uri='uri')",
            repr(Playlist(uri='uri', name='name')))

    def test_repr_with_tracks(self):
        self.assertEquals(
            "Playlist(name='name', tracks=[Track(artists=[], name='foo')], "
            "uri='uri')",
            repr(Playlist(uri='uri', name='name', tracks=[Track(name='foo')])))

    def test_eq_name(self):
        playlist1 = Playlist(name=u'name')
        playlist2 = Playlist(name=u'name')
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq_uri(self):
        playlist1 = Playlist(uri=u'uri')
        playlist2 = Playlist(uri=u'uri')
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq_tracks(self):
        tracks = [Track()]
        playlist1 = Playlist(tracks=tracks)
        playlist2 = Playlist(tracks=tracks)
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq_uri(self):
        playlist1 = Playlist(last_modified=1)
        playlist2 = Playlist(last_modified=1)
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq(self):
        tracks = [Track()]
        playlist1 = Playlist(uri=u'uri', name=u'name', tracks=tracks,
            last_modified=1)
        playlist2 = Playlist(uri=u'uri', name=u'name', tracks=tracks,
            last_modified=1)
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq_none(self):
        self.assertNotEqual(Playlist(), None)

    def test_eq_other(self):
        self.assertNotEqual(Playlist(), 'other')

    def test_ne_name(self):
        playlist1 = Playlist(name=u'name1')
        playlist2 = Playlist(name=u'name2')
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))

    def test_ne_uri(self):
        playlist1 = Playlist(uri=u'uri1')
        playlist2 = Playlist(uri=u'uri2')
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))

    def test_ne_tracks(self):
        playlist1 = Playlist(tracks=[Track(uri=u'uri1')])
        playlist2 = Playlist(tracks=[Track(uri=u'uri2')])
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))

    def test_ne_uri(self):
        playlist1 = Playlist(last_modified=1)
        playlist2 = Playlist(last_modified=2)
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))

    def test_ne(self):
        playlist1 = Playlist(uri=u'uri1', name=u'name2',
            tracks=[Track(uri=u'uri1')], last_modified=1)
        playlist2 = Playlist(uri=u'uri2', name=u'name2',
            tracks=[Track(uri=u'uri2')], last_modified=2)
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))

