from uuid import UUID

import pydantic
import pytest

from mopidy.models import Album, Artist


def test_uri():
    uri = "an_uri"
    album = Album(uri=uri)
    assert album.uri == uri
    with pytest.raises(pydantic.ValidationError):
        album.uri = None


def test_name():
    name = "a name"
    album = Album(name=name)
    assert album.name == name
    with pytest.raises(pydantic.ValidationError):
        album.name = None


def test_artists():
    artist = Artist()
    album = Album(artists=[artist])
    assert artist in album.artists
    with pytest.raises(pydantic.ValidationError):
        album.artists = None


def test_num_tracks():
    num_tracks = 11
    album = Album(num_tracks=num_tracks)
    assert album.num_tracks == num_tracks
    with pytest.raises(pydantic.ValidationError):
        album.num_tracks = None


def test_num_discs():
    num_discs = 2
    album = Album(num_discs=num_discs)
    assert album.num_discs == num_discs
    with pytest.raises(pydantic.ValidationError):
        album.num_discs = None


def test_date():
    date = "1977-01-01"
    album = Album(date=date)
    assert album.date == date
    with pytest.raises(pydantic.ValidationError):
        album.date = None


def test_musicbrainz_id():
    mb_id = "0383dadf-2a4e-4d10-a46a-e9e041da8eb3"
    album = Album(musicbrainz_id=mb_id)
    assert album.musicbrainz_id == UUID(mb_id)
    with pytest.raises(pydantic.ValidationError):
        album.musicbrainz_id = None


def test_invalid_kwarg():
    with pytest.raises(pydantic.ValidationError):
        Album(foo="baz")


def test_repr_without_artists():
    assert repr(Album(uri="uri", name="name")) == (
        "Album(uri='uri', name='name', artists=frozenset(), num_tracks=None, "
        "num_discs=None, date=None, musicbrainz_id=None)"
    )


def test_repr_with_artists():
    assert repr(Album(uri="uri", name="name", artists=[Artist(name="foo")])) == (
        "Album(uri='uri', name='name', artists=frozenset({Artist(uri=None, "
        "name='foo', sortname=None, musicbrainz_id=None)}), num_tracks=None, "
        "num_discs=None, date=None, musicbrainz_id=None)"
    )


def test_serialize_without_artists():
    assert Album(uri="uri", name="name").serialize() == {
        "__model__": "Album",
        "uri": "uri",
        "name": "name",
        "artists": [],
    }


def test_serialize_with_artists():
    artist = Artist(name="foo")
    assert Album(uri="uri", name="name", artists={artist}).serialize() == {
        "__model__": "Album",
        "uri": "uri",
        "name": "name",
        "artists": [artist.serialize()],
    }
