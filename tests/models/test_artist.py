from uuid import UUID

import pydantic
import pytest

from mopidy.models import Artist
from mopidy.types import Uri
from tests.factories import ArtistFactory


def test_uri():
    uri = "an_uri"
    artist = ArtistFactory.build(uri=uri)
    assert artist.uri == uri
    with pytest.raises(pydantic.ValidationError):
        artist.uri = None


def test_name():
    name = "a name"
    artist = ArtistFactory.build(name=name)
    assert artist.name == name
    with pytest.raises(pydantic.ValidationError):
        artist.name = None


def test_musicbrainz_id():
    mb_id = "0383dadf-2a4e-4d10-a46a-e9e041da8eb3"
    artist = ArtistFactory.build(musicbrainz_id=mb_id)
    assert artist.musicbrainz_id == UUID(mb_id)
    with pytest.raises(pydantic.ValidationError):
        artist.musicbrainz_id = None


def test_invalid_kwarg():
    with pytest.raises(pydantic.ValidationError):
        ArtistFactory.build(foo="baz")


def test_invalid_kwarg_with_name_matching_method():
    with pytest.raises(pydantic.ValidationError):
        ArtistFactory.build(replace="baz")

    with pytest.raises(pydantic.ValidationError):
        ArtistFactory.build(serialize="baz")


def test_repr():
    assert (
        repr(
            Artist(
                uri=Uri("uri"),
                name="name",
            )
        )
        == "Artist(uri='uri', name='name', sortname=None, musicbrainz_id=None)"
    )


def test_serialize():
    assert Artist(
        uri=Uri("uri"),
        name="name",
    ).serialize() == {
        "__model__": "Artist",
        "uri": "uri",
        "name": "name",
    }


def test_serialize_falsy_values():
    assert Artist(
        uri=Uri(""),
        name="",
    ).serialize() == {
        "__model__": "Artist",
        "uri": "",
        "name": "",
    }
