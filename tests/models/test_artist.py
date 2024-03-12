import pytest
from mopidy.models import Artist


def test_uri():
    uri = "an_uri"
    artist = Artist(uri=uri)
    assert artist.uri == uri
    with pytest.raises(AttributeError):
        artist.uri = None


def test_name():
    name = "a name"
    artist = Artist(name=name)
    assert artist.name == name
    with pytest.raises(AttributeError):
        artist.name = None


def test_musicbrainz_id():
    mb_id = "mb-id"
    artist = Artist(musicbrainz_id=mb_id)
    assert artist.musicbrainz_id == mb_id
    with pytest.raises(AttributeError):
        artist.musicbrainz_id = None


def test_invalid_kwarg():
    with pytest.raises(TypeError):
        Artist(foo="baz")


def test_invalid_kwarg_with_name_matching_method():
    with pytest.raises(TypeError):
        Artist(replace="baz")

    with pytest.raises(TypeError):
        Artist(serialize="baz")


def test_repr():
    assert repr(Artist(uri="uri", name="name")) == "Artist(uri='uri', name='name')"


def test_serialize():
    assert Artist(uri="uri", name="name").serialize() == {
        "__model__": "Artist",
        "uri": "uri",
        "name": "name",
    }


def test_serialize_falsy_values():
    assert Artist(uri="", name="").serialize() == {
        "__model__": "Artist",
        "uri": "",
        "name": "",
    }
