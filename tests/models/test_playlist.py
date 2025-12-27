import pydantic
import pytest

from mopidy.models import Playlist, Track
from mopidy.types import Uri
from tests.factories import PlaylistFactory, TrackFactory


def test_uri():
    uri = "an_uri"
    playlist = PlaylistFactory.build(uri=uri)
    assert playlist.uri == uri
    with pytest.raises(pydantic.ValidationError):
        playlist.uri = Uri("")


def test_name():
    name = "a name"
    playlist = PlaylistFactory.build(name=name)
    assert playlist.name == name
    with pytest.raises(pydantic.ValidationError):
        playlist.name = None


def test_tracks():
    tracks = TrackFactory.batch(3)
    playlist = PlaylistFactory.build(tracks=tracks)
    assert list(playlist.tracks) == tracks
    with pytest.raises(pydantic.ValidationError):
        playlist.tracks = ()


def test_length():
    tracks = TrackFactory.batch(3)
    playlist = PlaylistFactory.build(tracks=tracks)
    assert playlist.length == 3


def test_last_modified():
    last_modified = 1390942873000
    playlist = PlaylistFactory.build(last_modified=last_modified)
    assert playlist.last_modified == last_modified
    with pytest.raises(pydantic.ValidationError):
        playlist.last_modified = None


def test_with_new_uri():
    tracks = TrackFactory.batch(1)
    last_modified = 1390942873000
    playlist = PlaylistFactory.build(
        uri="an uri",
        name="a name",
        tracks=tracks,
        last_modified=last_modified,
    )
    new_playlist = playlist.replace(uri="another uri")
    assert new_playlist.uri == "another uri"
    assert new_playlist.name == "a name"
    assert list(new_playlist.tracks) == tracks
    assert new_playlist.last_modified == last_modified


def test_with_new_name():
    tracks = TrackFactory.batch(1)
    last_modified = 1390942873000
    playlist = PlaylistFactory.build(
        uri="an uri",
        name="a name",
        tracks=tracks,
        last_modified=last_modified,
    )
    new_playlist = playlist.replace(name="another name")
    assert new_playlist.uri == "an uri"
    assert new_playlist.name == "another name"
    assert list(new_playlist.tracks) == tracks
    assert new_playlist.last_modified == last_modified


def test_with_new_tracks():
    tracks = TrackFactory.batch(1)
    last_modified = 1390942873000
    playlist = PlaylistFactory.build(
        uri="an uri",
        name="a name",
        tracks=tracks,
        last_modified=last_modified,
    )
    new_tracks = TrackFactory.batch(2)
    new_playlist = playlist.replace(tracks=new_tracks)
    assert new_playlist.uri == "an uri"
    assert new_playlist.name == "a name"
    assert list(new_playlist.tracks) == new_tracks
    assert new_playlist.last_modified == last_modified


def test_with_new_last_modified():
    tracks = TrackFactory.batch(1)
    last_modified = 1390942873000
    new_last_modified = last_modified + 1000
    playlist = PlaylistFactory.build(
        uri="an uri",
        name="a name",
        tracks=tracks,
        last_modified=last_modified,
    )
    new_playlist = playlist.replace(last_modified=new_last_modified)
    assert new_playlist.uri == "an uri"
    assert new_playlist.name == "a name"
    assert list(new_playlist.tracks) == tracks
    assert new_playlist.last_modified == new_last_modified


def test_repr_without_tracks():
    assert (
        repr(Playlist(uri=Uri("uri"), name="name"))
        == "Playlist(uri='uri', name='name', tracks=(), last_modified=None)"
    )


def test_repr_with_tracks():
    assert repr(
        Playlist(
            uri=Uri("uri"),
            name="name",
            tracks=(Track(uri=Uri("uri"), name="foo"),),
        )
    ) == (
        "Playlist(uri='uri', name='name', tracks=(Track(uri='uri', name='foo', "
        "artists=frozenset(), album=None, composers=frozenset(), "
        "performers=frozenset(), genre=None, track_no=None, disc_no=None, date=None, "
        "length=None, bitrate=None, comment=None, musicbrainz_id=None, "
        "last_modified=None),), last_modified=None)"
    )


def test_serialize_without_tracks():
    assert Playlist(
        uri=Uri("uri"),
        name="name",
    ).serialize() == {
        "__model__": "Playlist",
        "uri": "uri",
        "name": "name",
        "tracks": [],
    }


def test_serialize_with_tracks():
    track = Track(uri=Uri("uri"), name="foo")
    assert Playlist(
        uri=Uri("uri"),
        name="name",
        tracks=(track,),
    ).serialize() == {
        "__model__": "Playlist",
        "uri": "uri",
        "name": "name",
        "tracks": [track.serialize()],
    }
