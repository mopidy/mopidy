import pydantic
import pytest

from mopidy.models import Ref
from mopidy.types import Uri


def test_uri():
    uri = "an_uri"
    ref = Ref.track(uri=Uri(uri), name="Foo")
    assert ref.uri == uri
    with pytest.raises(pydantic.ValidationError):
        ref.uri = Uri("")


def test_name():
    name = "a name"
    ref = Ref.track(uri=Uri("uri"), name=name)
    assert ref.name == name
    with pytest.raises(pydantic.ValidationError):
        ref.name = None


# TODO: add these for the more of the models?
def test_del_name():
    ref = Ref.track(uri=Uri("foo"), name="foo")
    with pytest.raises(pydantic.ValidationError):
        del ref.name


def test_repr_without_results():
    assert (
        repr(Ref.artist(uri=Uri("uri"), name="foo"))
        == "Ref(uri='uri', name='foo', type=ARTIST)"
    )


def test_serialize_without_results():
    assert Ref.track(
        uri=Uri("uri"),
        name=None,
    ).serialize() == {
        "__model__": "Ref",
        "type": "track",
        "uri": "uri",
    }


def test_type_constants():
    assert Ref.ALBUM == "album"
    assert Ref.ARTIST == "artist"
    assert Ref.DIRECTORY == "directory"
    assert Ref.PLAYLIST == "playlist"
    assert Ref.TRACK == "track"


def test_album_constructor():
    ref = Ref.album(uri=Uri("foo"), name="bar")
    assert ref.uri == "foo"
    assert ref.name == "bar"
    assert ref.type == Ref.ALBUM


def test_artist_constructor():
    ref = Ref.artist(uri=Uri("foo"), name="bar")
    assert ref.uri == "foo"
    assert ref.name == "bar"
    assert ref.type == Ref.ARTIST


def test_directory_constructor():
    ref = Ref.directory(uri=Uri("foo"), name="bar")
    assert ref.uri == "foo"
    assert ref.name == "bar"
    assert ref.type == Ref.DIRECTORY


def test_playlist_constructor():
    ref = Ref.playlist(uri=Uri("foo"), name="bar")
    assert ref.uri == "foo"
    assert ref.name == "bar"
    assert ref.type == Ref.PLAYLIST


def test_track_constructor():
    ref = Ref.track(uri=Uri("foo"), name="bar")
    assert ref.uri == "foo"
    assert ref.name == "bar"
    assert ref.type == Ref.TRACK
