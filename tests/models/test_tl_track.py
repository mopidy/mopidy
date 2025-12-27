import pydantic
import pytest

from mopidy.models import TlTrack, Track
from mopidy.types import TracklistId, Uri
from tests.factories import TrackFactory


def test_tlid():
    tlid = TracklistId(123)
    track = TrackFactory.build()
    tl_track = TlTrack(tlid=tlid, track=track)
    assert tl_track.tlid == tlid
    with pytest.raises(pydantic.ValidationError):
        tl_track.tlid = TracklistId(124)


def test_track():
    tlid = TracklistId(123)
    track = TrackFactory.build()
    tl_track = TlTrack(tlid=tlid, track=track)
    assert tl_track.track == track
    with pytest.raises(pydantic.ValidationError):
        tl_track.track = TrackFactory.build()


def test_positional_args():
    tlid = TracklistId(123)
    track = TrackFactory.build()
    tl_track = TlTrack(tlid, track)
    assert tl_track.tlid == tlid
    assert tl_track.track == track


def test_iteration():
    tlid = TracklistId(123)
    track = TrackFactory.build()
    tl_track = TlTrack(tlid, track)
    (tlid2, track2) = tl_track
    assert tlid2 == tlid
    assert track2 == track


def test_repr():
    assert repr(
        TlTrack(
            tlid=TracklistId(123),
            track=Track(uri=Uri("uri")),
        )
    ) == (
        "TlTrack(tlid=123, track=Track(uri='uri', name=None, artists=frozenset(), "
        "album=None, composers=frozenset(), performers=frozenset(), genre=None, "
        "track_no=None, disc_no=None, date=None, length=None, bitrate=None, "
        "comment=None, musicbrainz_id=None, last_modified=None))"
    )


def test_serialize():
    track = Track(uri=Uri("uri"), name="name")
    assert TlTrack(
        tlid=TracklistId(123),
        track=track,
    ).serialize() == {
        "__model__": "TlTrack",
        "tlid": 123,
        "track": track.serialize(),
    }
