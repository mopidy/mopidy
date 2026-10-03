import pydantic
import pytest

from mopidy.media import PlaylistEntry
from mopidy.models import Track


@pytest.mark.parametrize(
    "alternatives",
    [
        pytest.param((), id="empty"),
        pytest.param(("file:///b", "file:///a"), id="track-uri-not-first"),
    ],
)
def test_playlist_entry_alternatives_must_start_with_the_track_uri(alternatives):
    with pytest.raises(pydantic.ValidationError):
        PlaylistEntry(track=Track(uri="file:///a"), alternatives=alternatives)
