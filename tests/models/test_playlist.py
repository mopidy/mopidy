import pytest
from mopidy.models import Playlist, Track


def test_uri():
    uri = "an_uri"
    playlist = Playlist(uri=uri)
    assert playlist.uri == uri
    with pytest.raises(AttributeError):
        playlist.uri = None


def test_name():
    name = "a name"
    playlist = Playlist(name=name)
    assert playlist.name == name
    with pytest.raises(AttributeError):
        playlist.name = None


def test_tracks():
    tracks = [Track(), Track(), Track()]
    playlist = Playlist(tracks=tracks)
    assert list(playlist.tracks) == tracks
    with pytest.raises(AttributeError):
        playlist.tracks = None


def test_length():
    tracks = [Track(), Track(), Track()]
    playlist = Playlist(tracks=tracks)
    assert playlist.length == 3


def test_last_modified():
    last_modified = 1390942873000
    playlist = Playlist(last_modified=last_modified)
    assert playlist.last_modified == last_modified
    with pytest.raises(AttributeError):
        playlist.last_modified = None


def test_with_new_uri():
    tracks = [Track()]
    last_modified = 1390942873000
    playlist = Playlist(
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
    tracks = [Track()]
    last_modified = 1390942873000
    playlist = Playlist(
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
    tracks = [Track()]
    last_modified = 1390942873000
    playlist = Playlist(
        uri="an uri",
        name="a name",
        tracks=tracks,
        last_modified=last_modified,
    )
    new_tracks = [Track(), Track()]
    new_playlist = playlist.replace(tracks=new_tracks)
    assert new_playlist.uri == "an uri"
    assert new_playlist.name == "a name"
    assert list(new_playlist.tracks) == new_tracks
    assert new_playlist.last_modified == last_modified


def test_with_new_last_modified():
    tracks = [Track()]
    last_modified = 1390942873000
    new_last_modified = last_modified + 1000
    playlist = Playlist(
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


def test_invalid_kwarg():
    with pytest.raises(TypeError):
        Playlist(foo="baz")


def test_repr_without_tracks():
    assert repr(Playlist(uri="uri", name="name")) == "Playlist(uri='uri', name='name')"


def test_repr_with_tracks():
    assert (
        repr(Playlist(uri="uri", name="name", tracks=(Track(name="foo"),)))
        == "Playlist(uri='uri', name='name', tracks=(Track(name='foo'),))"
    )


def test_serialize_without_tracks():
    assert Playlist(uri="uri", name="name").serialize() == {
        "__model__": "Playlist",
        "uri": "uri",
        "name": "name",
    }


def test_serialize_with_tracks():
    track = Track(name="foo")
    assert Playlist(uri="uri", name="name", tracks=[track]).serialize() == {
        "__model__": "Playlist",
        "uri": "uri",
        "name": "name",
        "tracks": [track.serialize()],
    }
