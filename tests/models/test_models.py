from __future__ import absolute_import, unicode_literals

import json
import unittest

from mopidy.models import (
    Album, Artist, Image, ModelJSONEncoder, Playlist,
    Ref, SearchResult, TlTrack, Track, model_json_decoder)


class InheritanceTest(unittest.TestCase):

    def test_weakref_and_slots_play_nice_in_subclass(self):
        # Check that the following does not happen:
        # TypeError: Error when calling the metaclass bases
        #   __weakref__ slot disallowed: either we already got one...

        class Foo(Track):
            pass

    def test_sub_class_can_have_its_own_slots(self):
        # Needed for things like SpotifyTrack in mopidy-spotify 1.x

        class Foo(Track):
            __slots__ = ('_foo',)

        f = Foo()
        f._foo = 123

    def test_sub_class_can_be_initialized(self):
        # Fails with following error if fields are not handled across classes.
        #   TypeError: __init__() got an unexpected keyword argument "type"
        # Essentially this is testing that sub-classes take parent _fields into
        # account.

        class Foo(Ref):
            pass

        Foo.directory()


class CachingTest(unittest.TestCase):

    def test_same_instance(self):
        self.assertIs(Track(), Track())

    def test_same_instance_with_values(self):
        self.assertIs(Track(uri='test'), Track(uri='test'))

    def test_different_instance_with_different_values(self):
        self.assertIsNot(Track(uri='test1'), Track(uri='test2'))

    def test_different_instance_with_replace(self):
        t = Track(uri='test1')
        self.assertIsNot(t, t.replace(uri='test2'))


class GenericReplaceTest(unittest.TestCase):

    def compare(self, orig, other):
        self.assertEqual(orig, other)
        self.assertEqual(id(orig), id(other))

    def test_replace_track(self):
        track = Track()
        self.compare(track, track.replace())

    def test_replace_artist(self):
        artist = Artist()
        self.compare(artist, artist.replace())

    def test_replace_album(self):
        album = Album()
        self.compare(album, album.replace())

    def test_replace_playlist(self):
        playlist = Playlist()
        self.compare(playlist, playlist.replace())

    def test_replace_track_with_basic_values(self):
        track = Track(name='foo', uri='bar')
        other = track.replace(name='baz')
        self.assertEqual('baz', other.name)
        self.assertEqual('bar', other.uri)

    def test_replace_track_with_missing_values(self):
        track = Track(uri='bar')
        other = track.replace(name='baz')
        self.assertEqual('baz', other.name)
        self.assertEqual('bar', other.uri)

    def test_replace_track_with_private_internal_value(self):
        artist1 = Artist(name='foo')
        artist2 = Artist(name='bar')
        track = Track(artists=[artist1])
        other = track.replace(artists=[artist2])
        self.assertIn(artist2, other.artists)

    def test_replace_track_with_invalid_key(self):
        with self.assertRaises(TypeError):
            Track().replace(invalid_key=True)

    def test_replace_track_to_remove(self):
        track = Track(name='foo').replace(name=None)
        self.assertFalse(hasattr(track, '_name'))


class RefTest(unittest.TestCase):

    def test_uri(self):
        uri = 'an_uri'
        ref = Ref(uri=uri)
        self.assertEqual(ref.uri, uri)
        with self.assertRaises(AttributeError):
            ref.uri = None

    def test_name(self):
        name = 'a name'
        ref = Ref(name=name)
        self.assertEqual(ref.name, name)
        with self.assertRaises(AttributeError):
            ref.name = None

    # TODO: add these for the more of the models?
    def test_del_name(self):
        ref = Ref(name='foo')
        with self.assertRaises(AttributeError):
            del ref.name

    def test_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            Ref(foo='baz')

    def test_repr_without_results(self):
        self.assertEqual(
            "Ref(name=u'foo', type='artist', uri='uri')",
            repr(Ref(uri='uri', name='foo', type='artist')))

    def test_serialize_without_results(self):
        self.assertDictEqual(
            {'__model__': 'Ref', 'uri': 'uri'},
            Ref(uri='uri').serialize())

    def test_to_json_and_back(self):
        ref1 = Ref(uri='uri')
        serialized = json.dumps(ref1, cls=ModelJSONEncoder)
        ref2 = json.loads(serialized, object_hook=model_json_decoder)
        self.assertEqual(ref1, ref2)

    def test_type_constants(self):
        self.assertEqual(Ref.ALBUM, 'album')
        self.assertEqual(Ref.ARTIST, 'artist')
        self.assertEqual(Ref.DIRECTORY, 'directory')
        self.assertEqual(Ref.PLAYLIST, 'playlist')
        self.assertEqual(Ref.TRACK, 'track')

    def test_album_constructor(self):
        ref = Ref.album(uri='foo', name='bar')
        self.assertEqual(ref.uri, 'foo')
        self.assertEqual(ref.name, 'bar')
        self.assertEqual(ref.type, Ref.ALBUM)

    def test_artist_constructor(self):
        ref = Ref.artist(uri='foo', name='bar')
        self.assertEqual(ref.uri, 'foo')
        self.assertEqual(ref.name, 'bar')
        self.assertEqual(ref.type, Ref.ARTIST)

    def test_directory_constructor(self):
        ref = Ref.directory(uri='foo', name='bar')
        self.assertEqual(ref.uri, 'foo')
        self.assertEqual(ref.name, 'bar')
        self.assertEqual(ref.type, Ref.DIRECTORY)

    def test_playlist_constructor(self):
        ref = Ref.playlist(uri='foo', name='bar')
        self.assertEqual(ref.uri, 'foo')
        self.assertEqual(ref.name, 'bar')
        self.assertEqual(ref.type, Ref.PLAYLIST)

    def test_track_constructor(self):
        ref = Ref.track(uri='foo', name='bar')
        self.assertEqual(ref.uri, 'foo')
        self.assertEqual(ref.name, 'bar')
        self.assertEqual(ref.type, Ref.TRACK)


class ImageTest(unittest.TestCase):

    def test_uri(self):
        uri = 'an_uri'
        image = Image(uri=uri)
        self.assertEqual(image.uri, uri)
        with self.assertRaises(AttributeError):
            image.uri = None

    def test_width(self):
        image = Image(width=100)
        self.assertEqual(image.width, 100)
        with self.assertRaises(AttributeError):
            image.width = None

    def test_height(self):
        image = Image(height=100)
        self.assertEqual(image.height, 100)
        with self.assertRaises(AttributeError):
            image.height = None

    def test_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            Image(foo='baz')


class ArtistTest(unittest.TestCase):

    def test_uri(self):
        uri = 'an_uri'
        artist = Artist(uri=uri)
        self.assertEqual(artist.uri, uri)
        with self.assertRaises(AttributeError):
            artist.uri = None

    def test_name(self):
        name = 'a name'
        artist = Artist(name=name)
        self.assertEqual(artist.name, name)
        with self.assertRaises(AttributeError):
            artist.name = None

    def test_musicbrainz_id(self):
        mb_id = 'mb-id'
        artist = Artist(musicbrainz_id=mb_id)
        self.assertEqual(artist.musicbrainz_id, mb_id)
        with self.assertRaises(AttributeError):
            artist.musicbrainz_id = None

    def test_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            Artist(foo='baz')

    def test_invalid_kwarg_with_name_matching_method(self):
        with self.assertRaises(TypeError):
            Artist(replace='baz')

        with self.assertRaises(TypeError):
            Artist(serialize='baz')

    def test_repr(self):
        self.assertEqual(
            "Artist(name=u'name', uri='uri')",
            repr(Artist(uri='uri', name='name')))

    def test_serialize(self):
        self.assertDictEqual(
            {'__model__': 'Artist', 'uri': 'uri', 'name': 'name'},
            Artist(uri='uri', name='name').serialize())

    def test_serialize_falsy_values(self):
        self.assertDictEqual(
            {'__model__': 'Artist', 'uri': '', 'name': ''},
            Artist(uri='', name='').serialize())

    def test_to_json_and_back(self):
        artist1 = Artist(uri='uri', name='name')
        serialized = json.dumps(artist1, cls=ModelJSONEncoder)
        artist2 = json.loads(serialized, object_hook=model_json_decoder)
        self.assertEqual(artist1, artist2)

    def test_to_json_and_back_with_unknown_field(self):
        artist = Artist(uri='uri', name='name').serialize()
        artist['foo'] = 'foo'
        serialized = json.dumps(artist)
        with self.assertRaises(TypeError):
            json.loads(serialized, object_hook=model_json_decoder)

    def test_to_json_and_back_with_field_matching_method(self):
        artist = Artist(uri='uri', name='name').serialize()
        artist['copy'] = 'foo'
        serialized = json.dumps(artist)
        with self.assertRaises(TypeError):
            json.loads(serialized, object_hook=model_json_decoder)

    def test_to_json_and_back_with_field_matching_internal_field(self):
        artist = Artist(uri='uri', name='name').serialize()
        artist['__mro__'] = 'foo'
        serialized = json.dumps(artist)
        with self.assertRaises(TypeError):
            json.loads(serialized, object_hook=model_json_decoder)

    def test_eq_name(self):
        artist1 = Artist(name='name')
        artist2 = Artist(name='name')
        self.assertEqual(artist1, artist2)
        self.assertEqual(hash(artist1), hash(artist2))

    def test_eq_uri(self):
        artist1 = Artist(uri='uri')
        artist2 = Artist(uri='uri')
        self.assertEqual(artist1, artist2)
        self.assertEqual(hash(artist1), hash(artist2))

    def test_eq_musibrainz_id(self):
        artist1 = Artist(musicbrainz_id='id')
        artist2 = Artist(musicbrainz_id='id')
        self.assertEqual(artist1, artist2)
        self.assertEqual(hash(artist1), hash(artist2))

    def test_eq(self):
        artist1 = Artist(uri='uri', name='name', musicbrainz_id='id')
        artist2 = Artist(uri='uri', name='name', musicbrainz_id='id')
        self.assertEqual(artist1, artist2)
        self.assertEqual(hash(artist1), hash(artist2))

    def test_eq_none(self):
        self.assertNotEqual(Artist(), None)

    def test_eq_other(self):
        self.assertNotEqual(Artist(), 'other')

    def test_ne_name(self):
        artist1 = Artist(name='name1')
        artist2 = Artist(name='name2')
        self.assertNotEqual(artist1, artist2)
        self.assertNotEqual(hash(artist1), hash(artist2))

    def test_ne_uri(self):
        artist1 = Artist(uri='uri1')
        artist2 = Artist(uri='uri2')
        self.assertNotEqual(artist1, artist2)
        self.assertNotEqual(hash(artist1), hash(artist2))

    def test_ne_musicbrainz_id(self):
        artist1 = Artist(musicbrainz_id='id1')
        artist2 = Artist(musicbrainz_id='id2')
        self.assertNotEqual(artist1, artist2)
        self.assertNotEqual(hash(artist1), hash(artist2))

    def test_ne(self):
        artist1 = Artist(uri='uri1', name='name1', musicbrainz_id='id1')
        artist2 = Artist(uri='uri2', name='name2', musicbrainz_id='id2')
        self.assertNotEqual(artist1, artist2)
        self.assertNotEqual(hash(artist1), hash(artist2))


class AlbumTest(unittest.TestCase):

    def test_uri(self):
        uri = 'an_uri'
        album = Album(uri=uri)
        self.assertEqual(album.uri, uri)
        with self.assertRaises(AttributeError):
            album.uri = None

    def test_name(self):
        name = 'a name'
        album = Album(name=name)
        self.assertEqual(album.name, name)
        with self.assertRaises(AttributeError):
            album.name = None

    def test_artists(self):
        artist = Artist()
        album = Album(artists=[artist])
        self.assertIn(artist, album.artists)
        with self.assertRaises(AttributeError):
            album.artists = None

    def test_artists_none(self):
        self.assertEqual(set(), Album(artists=None).artists)

    def test_num_tracks(self):
        num_tracks = 11
        album = Album(num_tracks=num_tracks)
        self.assertEqual(album.num_tracks, num_tracks)
        with self.assertRaises(AttributeError):
            album.num_tracks = None

    def test_num_discs(self):
        num_discs = 2
        album = Album(num_discs=num_discs)
        self.assertEqual(album.num_discs, num_discs)
        with self.assertRaises(AttributeError):
            album.num_discs = None

    def test_date(self):
        date = '1977-01-01'
        album = Album(date=date)
        self.assertEqual(album.date, date)
        with self.assertRaises(AttributeError):
            album.date = None

    def test_musicbrainz_id(self):
        mb_id = 'mb-id'
        album = Album(musicbrainz_id=mb_id)
        self.assertEqual(album.musicbrainz_id, mb_id)
        with self.assertRaises(AttributeError):
            album.musicbrainz_id = None

    def test_images(self):
        image = 'data:foobar'
        album = Album(images=[image])
        self.assertIn(image, album.images)
        with self.assertRaises(AttributeError):
            album.images = None

    def test_images_none(self):
        self.assertEqual(set(), Album(images=None).images)

    def test_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            Album(foo='baz')

    def test_repr_without_artists(self):
        self.assertEqual(
            "Album(name=u'name', uri='uri')",
            repr(Album(uri='uri', name='name')))

    def test_repr_with_artists(self):
        self.assertEqual(
            "Album(artists=[Artist(name=u'foo')], name=u'name', uri='uri')",
            repr(Album(uri='uri', name='name', artists=[Artist(name='foo')])))

    def test_serialize_without_artists(self):
        self.assertDictEqual(
            {'__model__': 'Album', 'uri': 'uri', 'name': 'name'},
            Album(uri='uri', name='name').serialize())

    def test_serialize_with_artists(self):
        artist = Artist(name='foo')
        self.assertDictEqual(
            {'__model__': 'Album', 'uri': 'uri', 'name': 'name',
                'artists': [artist.serialize()]},
            Album(uri='uri', name='name', artists=[artist]).serialize())

    def test_serialize_with_images(self):
        image = 'data:foobar'
        self.assertDictEqual(
            {'__model__': 'Album', 'uri': 'uri', 'name': 'name',
                'images': [image]},
            Album(uri='uri', name='name', images=[image]).serialize())

    def test_to_json_and_back(self):
        album1 = Album(uri='uri', name='name', artists=[Artist(name='foo')])
        serialized = json.dumps(album1, cls=ModelJSONEncoder)
        album2 = json.loads(serialized, object_hook=model_json_decoder)
        self.assertEqual(album1, album2)

    def test_eq_name(self):
        album1 = Album(name='name')
        album2 = Album(name='name')
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_uri(self):
        album1 = Album(uri='uri')
        album2 = Album(uri='uri')
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_artists(self):
        artists = [Artist()]
        album1 = Album(artists=artists)
        album2 = Album(artists=artists)
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_artists_order(self):
        artist1 = Artist(name='name1')
        artist2 = Artist(name='name2')
        album1 = Album(artists=[artist1, artist2])
        album2 = Album(artists=[artist2, artist1])
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_num_tracks(self):
        album1 = Album(num_tracks=2)
        album2 = Album(num_tracks=2)
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_date(self):
        date = '1977-01-01'
        album1 = Album(date=date)
        album2 = Album(date=date)
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_musibrainz_id(self):
        album1 = Album(musicbrainz_id='id')
        album2 = Album(musicbrainz_id='id')
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq(self):
        artists = [Artist()]
        album1 = Album(
            name='name', uri='uri', artists=artists, num_tracks=2,
            musicbrainz_id='id')
        album2 = Album(
            name='name', uri='uri', artists=artists, num_tracks=2,
            musicbrainz_id='id')
        self.assertEqual(album1, album2)
        self.assertEqual(hash(album1), hash(album2))

    def test_eq_none(self):
        self.assertNotEqual(Album(), None)

    def test_eq_other(self):
        self.assertNotEqual(Album(), 'other')

    def test_ne_name(self):
        album1 = Album(name='name1')
        album2 = Album(name='name2')
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne_uri(self):
        album1 = Album(uri='uri1')
        album2 = Album(uri='uri2')
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne_artists(self):
        album1 = Album(artists=[Artist(name='name1')])
        album2 = Album(artists=[Artist(name='name2')])
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne_num_tracks(self):
        album1 = Album(num_tracks=1)
        album2 = Album(num_tracks=2)
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne_date(self):
        album1 = Album(date='1977-01-01')
        album2 = Album(date='1977-01-02')
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne_musicbrainz_id(self):
        album1 = Album(musicbrainz_id='id1')
        album2 = Album(musicbrainz_id='id2')
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))

    def test_ne(self):
        album1 = Album(
            name='name1', uri='uri1', artists=[Artist(name='name1')],
            num_tracks=1, musicbrainz_id='id1')
        album2 = Album(
            name='name2', uri='uri2', artists=[Artist(name='name2')],
            num_tracks=2, musicbrainz_id='id2')
        self.assertNotEqual(album1, album2)
        self.assertNotEqual(hash(album1), hash(album2))


class TrackTest(unittest.TestCase):

    def test_uri(self):
        uri = 'an_uri'
        track = Track(uri=uri)
        self.assertEqual(track.uri, uri)
        with self.assertRaises(AttributeError):
            track.uri = None

    def test_name(self):
        name = 'a name'
        track = Track(name=name)
        self.assertEqual(track.name, name)
        with self.assertRaises(AttributeError):
            track.name = None

    def test_artists(self):
        artists = [Artist(name='name1'), Artist(name='name2')]
        track = Track(artists=artists)
        self.assertEqual(set(track.artists), set(artists))
        with self.assertRaises(AttributeError):
            track.artists = None

    def test_artists_none(self):
        self.assertEqual(set(), Track(artists=None).artists)

    def test_composers(self):
        artists = [Artist(name='name1'), Artist(name='name2')]
        track = Track(composers=artists)
        self.assertEqual(set(track.composers), set(artists))
        with self.assertRaises(AttributeError):
            track.composers = None

    def test_composers_none(self):
        self.assertEqual(set(), Track(composers=None).composers)

    def test_performers(self):
        artists = [Artist(name='name1'), Artist(name='name2')]
        track = Track(performers=artists)
        self.assertEqual(set(track.performers), set(artists))
        with self.assertRaises(AttributeError):
            track.performers = None

    def test_performers_none(self):
        self.assertEqual(set(), Track(performers=None).performers)

    def test_album(self):
        album = Album()
        track = Track(album=album)
        self.assertEqual(track.album, album)
        with self.assertRaises(AttributeError):
            track.album = None

    def test_track_no(self):
        track_no = 7
        track = Track(track_no=track_no)
        self.assertEqual(track.track_no, track_no)
        with self.assertRaises(AttributeError):
            track.track_no = None

    def test_disc_no(self):
        disc_no = 2
        track = Track(disc_no=disc_no)
        self.assertEqual(track.disc_no, disc_no)
        with self.assertRaises(AttributeError):
            track.disc_no = None

    def test_date(self):
        date = '1977-01-01'
        track = Track(date=date)
        self.assertEqual(track.date, date)
        with self.assertRaises(AttributeError):
            track.date = None

    def test_length(self):
        length = 137000
        track = Track(length=length)
        self.assertEqual(track.length, length)
        with self.assertRaises(AttributeError):
            track.length = None

    def test_bitrate(self):
        bitrate = 160
        track = Track(bitrate=bitrate)
        self.assertEqual(track.bitrate, bitrate)
        with self.assertRaises(AttributeError):
            track.bitrate = None

    def test_musicbrainz_id(self):
        mb_id = 'mb-id'
        track = Track(musicbrainz_id=mb_id)
        self.assertEqual(track.musicbrainz_id, mb_id)
        with self.assertRaises(AttributeError):
            track.musicbrainz_id = None

    def test_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            Track(foo='baz')

    def test_repr_without_artists(self):
        self.assertEqual(
            "Track(name=u'name', uri='uri')",
            repr(Track(uri='uri', name='name')))

    def test_repr_with_artists(self):
        self.assertEqual(
            "Track(artists=[Artist(name=u'foo')], name=u'name', uri='uri')",
            repr(Track(uri='uri', name='name', artists=[Artist(name='foo')])))

    def test_serialize_without_artists(self):
        self.assertDictEqual(
            {'__model__': 'Track', 'uri': 'uri', 'name': 'name'},
            Track(uri='uri', name='name').serialize())

    def test_serialize_with_artists(self):
        artist = Artist(name='foo')
        self.assertDictEqual(
            {'__model__': 'Track', 'uri': 'uri', 'name': 'name',
                'artists': [artist.serialize()]},
            Track(uri='uri', name='name', artists=[artist]).serialize())

    def test_serialize_with_album(self):
        album = Album(name='foo')
        self.assertDictEqual(
            {'__model__': 'Track', 'uri': 'uri', 'name': 'name',
                'album': album.serialize()},
            Track(uri='uri', name='name', album=album).serialize())

    def test_to_json_and_back(self):
        track1 = Track(
            uri='uri', name='name', album=Album(name='foo'),
            artists=[Artist(name='foo')])
        serialized = json.dumps(track1, cls=ModelJSONEncoder)
        track2 = json.loads(serialized, object_hook=model_json_decoder)
        self.assertEqual(track1, track2)

    def test_eq_uri(self):
        track1 = Track(uri='uri1')
        track2 = Track(uri='uri1')
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_name(self):
        track1 = Track(name='name1')
        track2 = Track(name='name1')
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_artists(self):
        artists = [Artist()]
        track1 = Track(artists=artists)
        track2 = Track(artists=artists)
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_artists_order(self):
        artist1 = Artist(name='name1')
        artist2 = Artist(name='name2')
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
        date = '1977-01-01'
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
        track1 = Track(musicbrainz_id='id')
        track2 = Track(musicbrainz_id='id')
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq(self):
        date = '1977-01-01'
        artists = [Artist()]
        album = Album()
        track1 = Track(
            uri='uri', name='name', artists=artists, album=album, track_no=1,
            date=date, length=100, bitrate=100, musicbrainz_id='id')
        track2 = Track(
            uri='uri', name='name', artists=artists, album=album, track_no=1,
            date=date, length=100, bitrate=100, musicbrainz_id='id')
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_eq_none(self):
        self.assertNotEqual(Track(), None)

    def test_eq_other(self):
        self.assertNotEqual(Track(), 'other')

    def test_ne_uri(self):
        track1 = Track(uri='uri1')
        track2 = Track(uri='uri2')
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_name(self):
        track1 = Track(name='name1')
        track2 = Track(name='name2')
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_artists(self):
        track1 = Track(artists=[Artist(name='name1')])
        track2 = Track(artists=[Artist(name='name2')])
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_album(self):
        track1 = Track(album=Album(name='name1'))
        track2 = Track(album=Album(name='name2'))
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_track_no(self):
        track1 = Track(track_no=1)
        track2 = Track(track_no=2)
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne_date(self):
        track1 = Track(date='1977-01-01')
        track2 = Track(date='1977-01-02')
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
        track1 = Track(musicbrainz_id='id1')
        track2 = Track(musicbrainz_id='id2')
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ne(self):
        track1 = Track(
            uri='uri1', name='name1', artists=[Artist(name='name1')],
            album=Album(name='name1'), track_no=1, date='1977-01-01',
            length=100, bitrate=100, musicbrainz_id='id1')
        track2 = Track(
            uri='uri2', name='name2', artists=[Artist(name='name2')],
            album=Album(name='name2'), track_no=2, date='1977-01-02',
            length=200, bitrate=200, musicbrainz_id='id2')
        self.assertNotEqual(track1, track2)
        self.assertNotEqual(hash(track1), hash(track2))

    def test_ignores_values_with_default_value_none(self):
        track1 = Track(name='name1')
        track2 = Track(name='name1', album=None)
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))

    def test_replace_can_reset_to_default_value(self):
        track1 = Track(name='name1')
        track2 = Track(name='name1', album=Album()).replace(album=None)
        self.assertEqual(track1, track2)
        self.assertEqual(hash(track1), hash(track2))


class TlTrackTest(unittest.TestCase):

    def test_tlid(self):
        tlid = 123
        tl_track = TlTrack(tlid=tlid)
        self.assertEqual(tl_track.tlid, tlid)
        with self.assertRaises(AttributeError):
            tl_track.tlid = None

    def test_track(self):
        track = Track()
        tl_track = TlTrack(track=track)
        self.assertEqual(tl_track.track, track)
        with self.assertRaises(AttributeError):
            tl_track.track = None

    def test_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            TlTrack(foo='baz')

    def test_positional_args(self):
        tlid = 123
        track = Track()
        tl_track = TlTrack(tlid, track)
        self.assertEqual(tl_track.tlid, tlid)
        self.assertEqual(tl_track.track, track)

    def test_iteration(self):
        tlid = 123
        track = Track()
        tl_track = TlTrack(tlid, track)
        (tlid2, track2) = tl_track
        self.assertEqual(tlid2, tlid)
        self.assertEqual(track2, track)

    def test_repr(self):
        self.assertEqual(
            "TlTrack(tlid=123, track=Track(uri='uri'))",
            repr(TlTrack(tlid=123, track=Track(uri='uri'))))

    def test_serialize(self):
        track = Track(uri='uri', name='name')
        self.assertDictEqual(
            {'__model__': 'TlTrack', 'tlid': 123, 'track': track.serialize()},
            TlTrack(tlid=123, track=track).serialize())

    def test_to_json_and_back(self):
        tl_track1 = TlTrack(tlid=123, track=Track(uri='uri', name='name'))
        serialized = json.dumps(tl_track1, cls=ModelJSONEncoder)
        tl_track2 = json.loads(serialized, object_hook=model_json_decoder)
        self.assertEqual(tl_track1, tl_track2)

    def test_eq(self):
        tlid = 123
        track = Track()
        tl_track1 = TlTrack(tlid=tlid, track=track)
        tl_track2 = TlTrack(tlid=tlid, track=track)
        self.assertEqual(tl_track1, tl_track2)
        self.assertEqual(hash(tl_track1), hash(tl_track2))

    def test_eq_none(self):
        self.assertNotEqual(TlTrack(), None)

    def test_eq_other(self):
        self.assertNotEqual(TlTrack(), 'other')

    def test_ne_tlid(self):
        tl_track1 = TlTrack(tlid=123)
        tl_track2 = TlTrack(tlid=321)
        self.assertNotEqual(tl_track1, tl_track2)
        self.assertNotEqual(hash(tl_track1), hash(tl_track2))

    def test_ne_track(self):
        tl_track1 = TlTrack(track=Track(uri='a'))
        tl_track2 = TlTrack(track=Track(uri='b'))
        self.assertNotEqual(tl_track1, tl_track2)
        self.assertNotEqual(hash(tl_track1), hash(tl_track2))


class PlaylistTest(unittest.TestCase):

    def test_uri(self):
        uri = 'an_uri'
        playlist = Playlist(uri=uri)
        self.assertEqual(playlist.uri, uri)
        with self.assertRaises(AttributeError):
            playlist.uri = None

    def test_name(self):
        name = 'a name'
        playlist = Playlist(name=name)
        self.assertEqual(playlist.name, name)
        with self.assertRaises(AttributeError):
            playlist.name = None

    def test_tracks(self):
        tracks = [Track(), Track(), Track()]
        playlist = Playlist(tracks=tracks)
        self.assertEqual(list(playlist.tracks), tracks)
        with self.assertRaises(AttributeError):
            playlist.tracks = None

    def test_length(self):
        tracks = [Track(), Track(), Track()]
        playlist = Playlist(tracks=tracks)
        self.assertEqual(playlist.length, 3)

    def test_last_modified(self):
        last_modified = 1390942873000
        playlist = Playlist(last_modified=last_modified)
        self.assertEqual(playlist.last_modified, last_modified)
        with self.assertRaises(AttributeError):
            playlist.last_modified = None

    def test_with_new_uri(self):
        tracks = [Track()]
        last_modified = 1390942873000
        playlist = Playlist(
            uri='an uri', name='a name', tracks=tracks,
            last_modified=last_modified)
        new_playlist = playlist.replace(uri='another uri')
        self.assertEqual(new_playlist.uri, 'another uri')
        self.assertEqual(new_playlist.name, 'a name')
        self.assertEqual(list(new_playlist.tracks), tracks)
        self.assertEqual(new_playlist.last_modified, last_modified)

    def test_with_new_name(self):
        tracks = [Track()]
        last_modified = 1390942873000
        playlist = Playlist(
            uri='an uri', name='a name', tracks=tracks,
            last_modified=last_modified)
        new_playlist = playlist.replace(name='another name')
        self.assertEqual(new_playlist.uri, 'an uri')
        self.assertEqual(new_playlist.name, 'another name')
        self.assertEqual(list(new_playlist.tracks), tracks)
        self.assertEqual(new_playlist.last_modified, last_modified)

    def test_with_new_tracks(self):
        tracks = [Track()]
        last_modified = 1390942873000
        playlist = Playlist(
            uri='an uri', name='a name', tracks=tracks,
            last_modified=last_modified)
        new_tracks = [Track(), Track()]
        new_playlist = playlist.replace(tracks=new_tracks)
        self.assertEqual(new_playlist.uri, 'an uri')
        self.assertEqual(new_playlist.name, 'a name')
        self.assertEqual(list(new_playlist.tracks), new_tracks)
        self.assertEqual(new_playlist.last_modified, last_modified)

    def test_with_new_last_modified(self):
        tracks = [Track()]
        last_modified = 1390942873000
        new_last_modified = last_modified + 1000
        playlist = Playlist(
            uri='an uri', name='a name', tracks=tracks,
            last_modified=last_modified)
        new_playlist = playlist.replace(last_modified=new_last_modified)
        self.assertEqual(new_playlist.uri, 'an uri')
        self.assertEqual(new_playlist.name, 'a name')
        self.assertEqual(list(new_playlist.tracks), tracks)
        self.assertEqual(new_playlist.last_modified, new_last_modified)

    def test_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            Playlist(foo='baz')

    def test_repr_without_tracks(self):
        self.assertEqual(
            "Playlist(name=u'name', uri='uri')",
            repr(Playlist(uri='uri', name='name')))

    def test_repr_with_tracks(self):
        self.assertEqual(
            "Playlist(name=u'name', tracks=[Track(name=u'foo')], uri='uri')",
            repr(Playlist(uri='uri', name='name', tracks=[Track(name='foo')])))

    def test_serialize_without_tracks(self):
        self.assertDictEqual(
            {'__model__': 'Playlist', 'uri': 'uri', 'name': 'name'},
            Playlist(uri='uri', name='name').serialize())

    def test_serialize_with_tracks(self):
        track = Track(name='foo')
        self.assertDictEqual(
            {'__model__': 'Playlist', 'uri': 'uri', 'name': 'name',
                'tracks': [track.serialize()]},
            Playlist(uri='uri', name='name', tracks=[track]).serialize())

    def test_to_json_and_back(self):
        playlist1 = Playlist(uri='uri', name='name')
        serialized = json.dumps(playlist1, cls=ModelJSONEncoder)
        playlist2 = json.loads(serialized, object_hook=model_json_decoder)
        self.assertEqual(playlist1, playlist2)

    def test_eq_name(self):
        playlist1 = Playlist(name='name')
        playlist2 = Playlist(name='name')
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq_uri(self):
        playlist1 = Playlist(uri='uri')
        playlist2 = Playlist(uri='uri')
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq_tracks(self):
        tracks = [Track()]
        playlist1 = Playlist(tracks=tracks)
        playlist2 = Playlist(tracks=tracks)
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq_last_modified(self):
        playlist1 = Playlist(last_modified=1)
        playlist2 = Playlist(last_modified=1)
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq(self):
        tracks = [Track()]
        playlist1 = Playlist(
            uri='uri', name='name', tracks=tracks, last_modified=1)
        playlist2 = Playlist(
            uri='uri', name='name', tracks=tracks, last_modified=1)
        self.assertEqual(playlist1, playlist2)
        self.assertEqual(hash(playlist1), hash(playlist2))

    def test_eq_none(self):
        self.assertNotEqual(Playlist(), None)

    def test_eq_other(self):
        self.assertNotEqual(Playlist(), 'other')

    def test_ne_name(self):
        playlist1 = Playlist(name='name1')
        playlist2 = Playlist(name='name2')
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))

    def test_ne_uri(self):
        playlist1 = Playlist(uri='uri1')
        playlist2 = Playlist(uri='uri2')
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))

    def test_ne_tracks(self):
        playlist1 = Playlist(tracks=[Track(uri='uri1')])
        playlist2 = Playlist(tracks=[Track(uri='uri2')])
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))

    def test_ne_last_modified(self):
        playlist1 = Playlist(last_modified=1)
        playlist2 = Playlist(last_modified=2)
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))

    def test_ne(self):
        playlist1 = Playlist(
            uri='uri1', name='name1', tracks=[Track(uri='uri1')],
            last_modified=1)
        playlist2 = Playlist(
            uri='uri2', name='name2', tracks=[Track(uri='uri2')],
            last_modified=2)
        self.assertNotEqual(playlist1, playlist2)
        self.assertNotEqual(hash(playlist1), hash(playlist2))


class SearchResultTest(unittest.TestCase):

    def test_uri(self):
        uri = 'an_uri'
        result = SearchResult(uri=uri)
        self.assertEqual(result.uri, uri)
        with self.assertRaises(AttributeError):
            result.uri = None

    def test_tracks(self):
        tracks = [Track(), Track(), Track()]
        result = SearchResult(tracks=tracks)
        self.assertEqual(list(result.tracks), tracks)
        with self.assertRaises(AttributeError):
            result.tracks = None

    def test_artists(self):
        artists = [Artist(), Artist(), Artist()]
        result = SearchResult(artists=artists)
        self.assertEqual(list(result.artists), artists)
        with self.assertRaises(AttributeError):
            result.artists = None

    def test_albums(self):
        albums = [Album(), Album(), Album()]
        result = SearchResult(albums=albums)
        self.assertEqual(list(result.albums), albums)
        with self.assertRaises(AttributeError):
            result.albums = None

    def test_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            SearchResult(foo='baz')

    def test_repr_without_results(self):
        self.assertEqual(
            "SearchResult(uri='uri')",
            repr(SearchResult(uri='uri')))

    def test_serialize_without_results(self):
        self.assertDictEqual(
            {'__model__': 'SearchResult', 'uri': 'uri'},
            SearchResult(uri='uri').serialize())
