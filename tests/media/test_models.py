import pydantic
import pytest

from mopidy.media import PlaylistEntry
from mopidy.models import Track


def test_playlist_entry_track_uri_is_the_first_alternative():
    result = PlaylistEntry(
        track=Track(uri="file:///a"), alternatives=("file:///a", "file:///b")
    )

    assert result.track.uri == "file:///a"


def test_playlist_entry_needs_an_alternative():
    with pytest.raises(pydantic.ValidationError):
        PlaylistEntry(track=Track(uri="file:///a"), alternatives=())


def test_playlist_entry_track_uri_must_be_the_first_alternative():
    with pytest.raises(pydantic.ValidationError):
        PlaylistEntry(
            track=Track(uri="file:///a"), alternatives=("file:///b", "file:///a")
        )
