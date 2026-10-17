import gc
import weakref
from unittest import mock

import pytest

from mopidy._lib.gi import GLib, Gst
from mopidy._lib.paths import path_to_uri
from mopidy.media import MediaReaderError
from mopidy.media._gst.pipeline import GstReaderPipeline
from mopidy.media._gst.reader import GstMediaInfoReader, GstRead
from mopidy.media._gst.types import (
    GstAsyncDone,
    GstDurationChanged,
    GstEndOfStream,
    GstError,
    GstStreamFound,
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


def test_error_in_a_gstreamer_callback_gives_media_reader_error(mocker):
    make = Gst.ElementFactory.make
    mocker.patch.object(
        Gst.ElementFactory,
        "make",
        side_effect=lambda name, *args: (
            None if name == "fakesink" else make(name, *args)
        ),
    )
    uri = Uri(path_to_uri(path_to_data_dir("scanner/simple/song1.ogg")))

    with pytest.raises(MediaReaderError, match="fakesink"):
        GstMediaInfoReader().read_media_info(uri, timeout=DurationMs(1000))


def test_pipeline_is_freed_after_a_read():
    uri = Uri(path_to_uri(path_to_data_dir("scanner/simple/song1.ogg")))
    pipeline = GstReaderPipeline(uri)
    pipeline_ref = weakref.ref(pipeline)

    GstRead(uri, timeout=DurationMs(1000), pipeline=pipeline).run()
    del pipeline
    gc.collect()

    assert pipeline_ref() is None


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


def test_audio_stream_is_playable(read):
    assert read._on_message(GstStreamFound(mime="audio/mpeg", playable=True)) is False

    assert read._result().info.playable is True


def test_text_stream_ends_the_read(read):
    assert (
        read._on_message(GstStreamFound(mime="text/uri-list", playable=False)) is True
    )

    result = read._result()
    assert result.legacy_scanner_mime == "text/uri-list"
    assert result.info.playable is False


def test_end_of_stream_ends_the_read(read):
    assert read._on_message(GstEndOfStream()) is True


def test_error_raises_media_reader_error(read):
    with pytest.raises(MediaReaderError, match="bad"):
        read._on_message(make_error())


def test_async_done_with_tags_and_duration_ends_the_read(read, pipeline):
    read._on_message(GstTag({"title": ["a title"]}))

    assert read._on_message(GstAsyncDone()) is True

    assert read._result().info.track.length == 4704
    pipeline.set_state.assert_not_called()


def test_async_done_without_tags_starts_playing(read, pipeline):
    assert read._on_message(GstAsyncDone()) is False

    pipeline.set_state.assert_called_once_with(Gst.State.PLAYING)


def test_async_done_without_tags_ends_the_read_if_playing_fails(read, pipeline):
    pipeline.set_state.return_value = False

    assert read._on_message(GstAsyncDone()) is True


def test_async_done_without_tags_ends_the_read_if_not_seekable(read, pipeline):
    pipeline.query_seekable.return_value = False

    assert read._on_message(GstAsyncDone()) is True

    pipeline.set_state.assert_not_called()


def test_duration_change_without_tags_is_ignored(read, pipeline):
    assert read._on_message(GstDurationChanged()) is False

    pipeline.query_duration.assert_not_called()


def test_duration_change_with_tags_ends_the_read(read, pipeline):
    read._on_message(GstTag({"title": ["a title"]}))

    assert read._on_message(GstDurationChanged()) is True

    assert read._result().info.track.length == 4704
    pipeline.set_state.assert_called_once_with(Gst.State.PAUSED)


def test_run_tears_down_the_pipeline_after_an_error(read, pipeline):
    pipeline.pop_message.return_value = make_error()

    with pytest.raises(MediaReaderError):
        read.run()

    pipeline.teardown.assert_called_once_with()
