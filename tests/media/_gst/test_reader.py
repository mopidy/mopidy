from unittest import mock

import pytest

from mopidy._lib.gi import GLib, Gst
from mopidy._lib.paths import path_to_uri
from mopidy.media import MediaReaderError
from mopidy.media._gst.pipeline import GstReaderPipeline
from mopidy.media._gst.reader import GstMediaInfoReader, GstRead
from mopidy.media._gst.types import (
    GstError,
    GstTag,
)
from mopidy.types import DurationMs, Uri
from tests import path_to_data_dir


def test_tags_that_are_not_valid_are_left_out():
    pipeline = mock.Mock(spec=GstReaderPipeline)
    pipeline.query_seekable.return_value = True
    read = GstRead(Uri("file:///song.ogg"), timeout=DurationMs(1000), pipeline=pipeline)

    # Track does not accept a negative track number or track count.
    read._on_message(
        GstTag(
            {
                "title": ["a title"],
                "track-number": [-1],
                "album": ["an album"],
                "track-count": [-2],
            }
        )
    )

    track = read._result().info.track
    assert track.name == "a title"
    assert track.track_no is None
    assert track.album is not None
    assert track.album.name == "an album"
    assert track.album.num_tracks is None


def test_element_that_cannot_be_made_gives_media_reader_error(mocker):
    mocker.patch.object(Gst.ElementFactory, "make", return_value=None)
    uri = Uri(path_to_uri(path_to_data_dir("scanner/simple/song1.ogg")))

    with pytest.raises(MediaReaderError):
        GstMediaInfoReader().read_media_info(uri, timeout=DurationMs(1000))


@pytest.fixture
def pipeline():
    pipeline = mock.Mock(spec=GstReaderPipeline)
    pipeline.query_duration.return_value = (True, DurationMs(4704))
    pipeline.query_seekable.return_value = True
    pipeline.set_state.return_value = True
    return pipeline


@pytest.fixture
def read(pipeline):
    return GstRead(Uri("file:///song.ogg"), timeout=DurationMs(1000), pipeline=pipeline)


def make_error():
    return GstError(
        GLib.Error.new_literal(Gst.CoreError.quark(), "bad", Gst.CoreError.FAILED),
        "debug text",
    )


def test_run_tears_down_the_pipeline_after_an_error(read, pipeline):
    pipeline.pop_message.return_value = make_error()

    with pytest.raises(MediaReaderError):
        read.run()

    pipeline.teardown.assert_called_once_with()
