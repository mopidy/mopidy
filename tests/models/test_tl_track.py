import pytest
from mopidy.models import TlTrack, Track


def test_tlid():
    tlid = 123
    track = Track()
    tl_track = TlTrack(tlid=tlid, track=track)
    assert tl_track.tlid == tlid
    with pytest.raises(AttributeError):
        tl_track.tlid = None


def test_track():
    tlid = 123
    track = Track()
    tl_track = TlTrack(tlid=tlid, track=track)
    assert tl_track.track == track
    with pytest.raises(AttributeError):
        tl_track.track = None


def test_invalid_kwarg():
    with pytest.raises(TypeError):
        TlTrack(foo="baz")


def test_positional_args():
    tlid = 123
    track = Track()
    tl_track = TlTrack(tlid, track)
    assert tl_track.tlid == tlid
    assert tl_track.track == track


def test_iteration():
    tlid = 123
    track = Track()
    tl_track = TlTrack(tlid, track)
    (tlid2, track2) = tl_track
    assert tlid2 == tlid
    assert track2 == track


def test_repr():
    assert (
        repr(TlTrack(tlid=123, track=Track(uri="uri")))
        == "TlTrack(tlid=123, track=Track(uri='uri'))"
    )


def test_serialize():
    track = Track(uri="uri", name="name")
    assert TlTrack(tlid=123, track=track).serialize() == {
        "__model__": "TlTrack",
        "tlid": 123,
        "track": track.serialize(),
    }
