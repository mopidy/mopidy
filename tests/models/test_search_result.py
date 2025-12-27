import pydantic
import pytest

from mopidy.models import SearchResult
from mopidy.types import Uri
from tests.factories import (
    AlbumFactory,
    ArtistFactory,
    SearchResultFactory,
    TrackFactory,
)


def test_uri():
    uri = "an_uri"
    result = SearchResultFactory.build(uri=uri)
    assert result.uri == uri
    with pytest.raises(pydantic.ValidationError):
        result.uri = None


def test_tracks():
    tracks = TrackFactory.batch(3)
    result = SearchResultFactory.build(tracks=tracks)
    assert list(result.tracks) == tracks
    with pytest.raises(pydantic.ValidationError):
        result.tracks = ()


def test_artists():
    artists = ArtistFactory.batch(3)
    result = SearchResultFactory.build(artists=artists)
    assert list(result.artists) == artists
    with pytest.raises(pydantic.ValidationError):
        result.artists = ()


def test_albums():
    albums = AlbumFactory.batch(3)
    result = SearchResultFactory.build(albums=albums)
    assert list(result.albums) == albums
    with pytest.raises(pydantic.ValidationError):
        result.albums = ()


def test_repr_without_results():
    assert (
        repr(SearchResult(uri=Uri("uri")))
        == "SearchResult(uri='uri', tracks=(), artists=(), albums=())"
    )


def test_serialize_without_results():
    assert SearchResult(uri=Uri("uri")).serialize() == {
        "__model__": "SearchResult",
        "uri": "uri",
        "albums": [],
        "artists": [],
        "tracks": [],
    }
