from uuid import UUID

import pydantic
import pytest

from mopidy.models import Album, Artist
from mopidy.types import Uri
from tests.factories import AlbumFactory, ArtistFactory


def test_uri():
    uri = "an_uri"
    album = AlbumFactory.build(uri=uri)
    assert album.uri == uri
    with pytest.raises(pydantic.ValidationError):
        album.uri = None


def test_name():
    name = "a name"
    album = AlbumFactory.build(name=name)
    assert album.name == name
    with pytest.raises(pydantic.ValidationError):
        album.name = None


def test_artists():
    artist = ArtistFactory.build()
    album = AlbumFactory.build(artists=[artist])
    assert artist in album.artists
    with pytest.raises(pydantic.ValidationError):
        album.artists = frozenset()


def test_num_tracks():
    num_tracks = 11
    album = AlbumFactory.build(num_tracks=num_tracks)
    assert album.num_tracks == num_tracks
    with pytest.raises(pydantic.ValidationError):
        album.num_tracks = None


def test_num_discs():
    num_discs = 2
    album = AlbumFactory.build(num_discs=num_discs)
    assert album.num_discs == num_discs
    with pytest.raises(pydantic.ValidationError):
        album.num_discs = None


def test_date():
    date = "1977-01-01"
    album = AlbumFactory.build(date=date)
    assert album.date == date
    with pytest.raises(pydantic.ValidationError):
        album.date = None


def test_musicbrainz_id():
    mb_id = "0383dadf-2a4e-4d10-a46a-e9e041da8eb3"
    album = AlbumFactory.build(musicbrainz_id=mb_id)
    assert album.musicbrainz_id == UUID(mb_id)
    with pytest.raises(pydantic.ValidationError):
        album.musicbrainz_id = None


def test_invalid_kwarg():
    with pytest.raises(pydantic.ValidationError):
        AlbumFactory.build(foo="baz")


def test_repr_without_artists():
    assert repr(
        Album(uri=Uri("uri"), name="name"),
    ) == (
        "Album(uri='uri', name='name', artists=frozenset(), num_tracks=None, "
        "num_discs=None, date=None, musicbrainz_id=None)"
    )


def test_repr_with_artists():
    assert repr(
        Album(
            uri=Uri("uri"),
            name="name",
            artists=frozenset({Artist(name="foo")}),
        )
    ) == (
        "Album(uri='uri', name='name', artists=frozenset({Artist(uri=None, "
        "name='foo', sortname=None, musicbrainz_id=None)}), num_tracks=None, "
        "num_discs=None, date=None, musicbrainz_id=None)"
    )


def test_serialize_without_artists():
    assert Album(
        uri=Uri("uri"),
        name="name",
    ).serialize() == {
        "__model__": "Album",
        "uri": "uri",
        "name": "name",
        "artists": [],
    }


def test_serialize_with_artists():
    artist = Artist(name="foo")
    assert Album(
        uri=Uri("uri"),
        name="name",
        artists=frozenset({artist}),
    ).serialize() == {
        "__model__": "Album",
        "uri": "uri",
        "name": "name",
        "artists": [artist.serialize()],
    }
