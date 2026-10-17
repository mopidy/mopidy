import pytest

from mopidy._lib.gi import GLib, Gst, GstPbutils
from mopidy._lib.paths import path_to_uri
from mopidy.media import MediaReaderError
from mopidy.media._gst import types
from mopidy.media._gst.pipeline import GstReaderPipeline
from tests import path_to_data_dir


@pytest.fixture
def pipeline():
    uri = path_to_uri(path_to_data_dir("scanner/simple/song1.ogg"))
    pipeline = GstReaderPipeline(uri)
    yield pipeline
    pipeline.teardown()


def test_uri_scheme_without_a_source_element_gives_media_reader_error():
    with pytest.raises(MediaReaderError, match="nosuchscheme"):
        GstReaderPipeline("nosuchscheme:foo")


@pytest.fixture
def element():
    return Gst.ElementFactory.make("fakesink")


def test_decode_bus_message_decodes_the_stream_found_by_parsebin(pipeline, element):
    structure = Gst.Structure.new_empty("mopidy-stream-found")
    structure.set_value("mime", "audio/mpeg")
    message = Gst.Message.new_application(element, structure)

    assert pipeline._decode_bus_message(message) == types.GstStreamFound("audio/mpeg")


def test_decode_bus_message_drops_other_application_messages(pipeline, element):
    structure = Gst.Structure.new_empty("something-else")
    message = Gst.Message.new_application(element, structure)

    assert pipeline._decode_bus_message(message) is None


def test_decode_bus_message_decodes_the_mime_of_a_missing_plugin(pipeline, element):
    caps = Gst.Caps.from_string("audio/x-unknown")
    message = GstPbutils.missing_decoder_message_new(element, caps)

    assert pipeline._decode_bus_message(message) == types.GstMissingPlugin(
        "audio/x-unknown"
    )


def test_decode_bus_message_decodes_an_error(pipeline, element):
    error = GLib.Error.new_literal(Gst.CoreError.quark(), "bad", Gst.CoreError.FAILED)
    message = Gst.Message.new_error(element, error, "debug text")

    decoded = pipeline._decode_bus_message(message)

    assert isinstance(decoded, types.GstError)
    assert decoded.debug == "debug text"


def test_decode_bus_message_decodes_a_duration_change(pipeline, element):
    message = Gst.Message.new_duration_changed(element)

    assert pipeline._decode_bus_message(message) == types.GstDurationChanged()


def test_decode_bus_message_converts_the_tags(pipeline, element):
    taglist = Gst.TagList.new_empty()
    taglist.add_value(Gst.TagMergeMode.APPEND, "title", "a title")
    message = Gst.Message.new_tag(element, taglist)

    assert pipeline._decode_bus_message(message) == types.GstTag({"title": ["a title"]})


def test_decode_bus_message_drops_what_the_reader_ignores(pipeline, element):
    message = Gst.Message.new_latency(element)

    assert pipeline._decode_bus_message(message) is None
