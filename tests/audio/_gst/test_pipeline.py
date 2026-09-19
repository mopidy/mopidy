from unittest import mock

import pytest

from mopidy import exceptions
from mopidy._lib.gi import Gst
from mopidy.audio._gst.pipeline import (
    GST_PLAY_FLAGS_AUDIO,
    GST_PLAY_FLAGS_DOWNLOAD,
    GstOutputBin,
    GstPipeline,
    make_output_bin,
)


@pytest.fixture
def pipeline():
    config = {
        "audio": {
            "output": "testoutput",
            "buffer_time": None,
        },
    }
    pipeline = GstPipeline(
        config,
        on_message=mock.Mock(),
        on_position=mock.Mock(),
        on_about_to_finish=mock.Mock(),
        on_source_setup=mock.Mock(),
    )
    yield pipeline
    pipeline.teardown()


def test_download_flag_is_passed_to_playbin_if_download_buffering_is_enabled(pipeline):
    pipeline.set_uri("some:uri", download=True)

    flags = pipeline.playbin.get_property("flags")
    assert flags == GST_PLAY_FLAGS_AUDIO | GST_PLAY_FLAGS_DOWNLOAD


def test_download_flag_is_not_passed_to_playbin_if_download_buffering_is_disabled(
    pipeline,
):
    pipeline.set_uri("some:uri", download=False)

    flags = pipeline.playbin.get_property("flags")
    assert flags == GST_PLAY_FLAGS_AUDIO


def test_set_uri_sets_the_uri_on_the_playbin(pipeline):
    pipeline.set_uri("file:///tmp/foo.mp3")

    assert pipeline.playbin.get_property("uri") == "file:///tmp/foo.mp3"


def test_get_position_is_zero_before_playback(pipeline):
    assert pipeline.get_position() == 0


def test_set_state_returns_true_on_success(pipeline):
    assert pipeline.set_state(Gst.State.READY) is True


def test_make_output_bin_uses_a_fakesink_for_the_test_output():
    output_bin = make_output_bin("testoutput")

    assert not isinstance(output_bin, GstOutputBin)
    assert output_bin.get_factory().get_name() == "fakesink"


def test_make_output_bin_builds_the_described_output():
    output_bin = make_output_bin("fakesink")

    assert isinstance(output_bin, GstOutputBin)
    assert output_bin.get_static_pad("sink") is not None


def test_output_bin_takes_more_than_one_output():
    output_bin = GstOutputBin()
    output_bin.add_output("fakesink")
    output_bin.add_output("fakesink")

    assert output_bin.numchildren == 5  # tee, and a queue plus a bin per output


def test_output_bin_rejects_an_unknown_output():
    output_bin = GstOutputBin()

    with pytest.raises(exceptions.AudioException):
        output_bin.add_output("definitelynotanelement")
