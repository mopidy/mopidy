import pydantic
import pytest

from tests.factories import ArtistFactory, TrackFactory


def test_replace_track_with_basic_values():
    track = TrackFactory.build(uri="bar", name="foo")

    other = track.replace(name="baz")

    assert other.uri == "bar"
    assert other.name == "baz"


def test_replace_track_with_missing_values():
    track = TrackFactory.build(uri="bar")

    other = track.replace(name="baz")

    assert other.uri == "bar"
    assert other.name == "baz"


def test_replace_track_with_private_internal_value():
    artist1 = ArtistFactory.build(name="foo")
    artist2 = ArtistFactory.build(name="bar")
    track = TrackFactory.build(artists=[artist1])

    other = track.replace(artists=[artist2])

    assert artist2 in other.artists


def test_replace_track_with_invalid_key():
    with pytest.raises(pydantic.ValidationError):
        TrackFactory.build().replace(invalid_key=True)
