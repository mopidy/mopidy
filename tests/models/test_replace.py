import pytest
from mopidy.models import Artist, Track


def test_replace_track_with_basic_values():
    track = Track(name="foo", uri="bar")
    other = track.replace(name="baz")
    assert other.name == "baz"
    assert other.uri == "bar"


def test_replace_track_with_missing_values():
    track = Track(uri="bar")
    other = track.replace(name="baz")
    assert other.name == "baz"
    assert other.uri == "bar"


def test_replace_track_with_private_internal_value():
    artist1 = Artist(name="foo")
    artist2 = Artist(name="bar")
    track = Track(artists=[artist1])
    other = track.replace(artists=[artist2])
    assert artist2 in other.artists


def test_replace_track_with_invalid_key():
    with pytest.raises(TypeError):
        Track().replace(invalid_key=True)


def test_replace_track_to_remove():
    track = Track(name="foo").replace(name=None)
    assert not hasattr(track, "_name")
