from uuid import UUID

import pydantic
import pytest

from mopidy.models import Album, Artist, Track
from mopidy.types import Uri
from tests.factories import AlbumFactory, ArtistFactory, TrackFactory


def test_uri():
    uri = "an_uri"
    track = TrackFactory.build(uri=uri)
    assert track.uri == uri
    with pytest.raises(pydantic.ValidationError):
        track.uri = Uri("")


def test_name():
    name = "a name"
    track = TrackFactory.build(name=name)
    assert track.name == name
    with pytest.raises(pydantic.ValidationError):
        track.name = None


def test_artists():
    artists = ArtistFactory.batch(2)
    track = TrackFactory.build(artists=artists)
    assert set(track.artists) == set(artists)
    with pytest.raises(pydantic.ValidationError):
        track.artists = frozenset()


def test_composers():
    artists = ArtistFactory.batch(2)
    track = TrackFactory.build(composers=artists)
    assert set(track.composers) == set(artists)
    with pytest.raises(pydantic.ValidationError):
        track.composers = frozenset()


def test_performers():
    artists = ArtistFactory.batch(2)
    track = TrackFactory.build(performers=artists)
    assert set(track.performers) == set(artists)
    with pytest.raises(pydantic.ValidationError):
        track.performers = frozenset()


def test_album():
    album = AlbumFactory.build()
    track = TrackFactory.build(album=album)
    assert track.album == album
    with pytest.raises(pydantic.ValidationError):
        track.album = AlbumFactory.build()


def test_track_no():
    track_no = 7
    track = TrackFactory.build(track_no=track_no)
    assert track.track_no == track_no
    with pytest.raises(pydantic.ValidationError):
        track.track_no = None


def test_disc_no():
    disc_no = 2
    track = TrackFactory.build(disc_no=disc_no)
    assert track.disc_no == disc_no
    with pytest.raises(pydantic.ValidationError):
        track.disc_no = None


def test_date():
    date = "1977-01-01"
    track = TrackFactory.build(date=date)
    assert track.date == date
    with pytest.raises(pydantic.ValidationError):
        track.date = None


def test_length():
    length = 137000
    track = TrackFactory.build(length=length)
    assert track.length == length
    with pytest.raises(pydantic.ValidationError):
        track.length = None


def test_bitrate():
    bitrate = 160
    track = TrackFactory.build(bitrate=bitrate)
    assert track.bitrate == bitrate
    with pytest.raises(pydantic.ValidationError):
        track.bitrate = None


def test_musicbrainz_id():
    mb_id = "0383dadf-2a4e-4d10-a46a-e9e041da8eb3"
    track = TrackFactory.build(musicbrainz_id=mb_id)
    assert track.musicbrainz_id == UUID(mb_id)
    with pytest.raises(pydantic.ValidationError):
        track.musicbrainz_id = None


def test_repr_without_artists():
    assert repr(
        Track(
            uri=Uri("uri"),
            name="name",
        )
    ) == (
        "Track(uri='uri', name='name', artists=frozenset(), album=None, "
        "composers=frozenset(), performers=frozenset(), genre=None, track_no=None, "
        "disc_no=None, date=None, length=None, bitrate=None, comment=None, "
        "musicbrainz_id=None, last_modified=None)"
    )


def test_repr_with_artists():
    assert repr(
        Track(
            uri=Uri("uri"),
            name="name",
            artists=frozenset({Artist(name="foo")}),
        )
    ) == (
        "Track(uri='uri', name='name', artists=frozenset({Artist(uri=None, name='foo', "
        "sortname=None, musicbrainz_id=None)}), album=None, composers=frozenset(), "
        "performers=frozenset(), genre=None, track_no=None, disc_no=None, date=None, "
        "length=None, bitrate=None, comment=None, musicbrainz_id=None, "
        "last_modified=None)"
    )


def test_serialize_without_artists():
    assert Track(
        uri=Uri("uri"),
        name="name",
    ).serialize() == {
        "__model__": "Track",
        "uri": "uri",
        "name": "name",
        "artists": [],
        "composers": [],
        "performers": [],
    }


def test_serialize_with_artists():
    artist = Artist(name="foo")
    assert Track(
        uri=Uri("uri"),
        name="name",
        artists=frozenset({artist}),
    ).serialize() == {
        "__model__": "Track",
        "uri": "uri",
        "name": "name",
        "artists": [artist.serialize()],
        "composers": [],
        "performers": [],
    }


def test_serialize_with_album():
    album = Album(name="foo")
    assert Track(
        uri=Uri("uri"),
        name="name",
        album=album,
    ).serialize() == {
        "__model__": "Track",
        "uri": "uri",
        "name": "name",
        "artists": [],
        "album": album.serialize(),
        "composers": [],
        "performers": [],
    }
