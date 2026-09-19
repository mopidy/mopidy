import pytest

from mopidy import exceptions
from mopidy.audio._gst.pipeline import GstOutputBin, make_output_bin


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
