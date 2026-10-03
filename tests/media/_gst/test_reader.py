from mopidy.media._gst.pipeline import GstMediaData
from mopidy.media._gst.reader import GstMediaInfoReader
from mopidy.types import DurationMs, Uri


def test_tags_that_are_not_valid_are_left_out(mocker):
    # Track does not accept a negative track number or track count.
    mocker.patch(
        "mopidy.media._gst.reader.read_media_data",
        return_value=GstMediaData(
            tags={
                "title": ["a title"],
                "track-number": [-1],
                "album": ["an album"],
                "track-count": [-2],
            },
            duration=DurationMs(4704),
            seekable=True,
            mime=None,
            playable=True,
        ),
    )

    info = GstMediaInfoReader().read_media_info(
        Uri("file:///song.ogg"), timeout=DurationMs(1000)
    )

    assert info.playable is True
    assert info.track.name == "a title"
    assert info.track.length == 4704
    assert info.track.track_no is None
    assert info.track.album is not None
    assert info.track.album.name == "an album"
    assert info.track.album.num_tracks is None
