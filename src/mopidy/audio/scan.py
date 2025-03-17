import logging
import time
from enum import IntEnum
from pathlib import Path
from typing import Any, NamedTuple, cast

from mopidy import exceptions
from mopidy.audio import tags as tags_lib
from mopidy.audio import utils
from mopidy.internal import log
from mopidy.internal.gi import Gst, GstPbutils


class GstElementFactoryListType(IntEnum):
    DECODER = 1 << 0
    AUDIO = 1 << 50
    DEMUXER = 1 << 5
    DEPAYLOADER = 1 << 8
    PARSER = 1 << 6


class GstAutoplugSelectResult(IntEnum):
    TRY = 0
    EXPOSE = 1
    SKIP = 2


class _Result(NamedTuple):
    uri: str
    tags: dict[str, Any]
    duration: int | None
    seekable: bool
    mime: str | None
    playable: bool


logger = logging.getLogger(__name__)


def _trace(*args, **kwargs):
    logger.log(log.TRACE_LOG_LEVEL, *args, **kwargs)


# TODO: replace with a scan(uri, timeout=1000, proxy_config=None)?
class Scanner:
    """Helper to get tags and other relevant info from URIs.

    :param timeout: timeout for scanning a URI in ms
    :param proxy_config: dictionary containing proxy config strings.
    """

    def __init__(
        self,
        timeout: int = 1000,
        proxy_config: dict[str, Any] | None = None,
    ) -> None:
        self._timeout_ms = int(timeout)
        self._proxy_config = proxy_config or {}

    def scan(
        self,
        uri: str,
        timeout: float | None = None,
    ) -> _Result:
        """Scan the given uri collecting relevant metadata.

        :param uri: URI of the resource to scan.
        :type uri: string
        :param timeout: timeout for scanning a URI in ms. Defaults to the
            ``timeout`` value used when creating the scanner.
        :type timeout: int
        :return: A named tuple containing
            ``(uri, tags, duration, seekable, mime)``.
            ``tags`` is a dictionary of lists for all the tags we found.
            ``duration`` is the length of the URI in milliseconds, or
            :class:`None` if the URI has no duration. ``seekable`` is boolean.
            indicating if a seek would succeed.
        """
        timeout = int(timeout or self._timeout_ms)
        pipeline, signals = _setup_pipeline(uri, self._proxy_config)

        try:
            _start_pipeline(pipeline)
            tags, mime, have_audio, duration = _process(pipeline, timeout)
            seekable = _query_seekable(pipeline)
            return _Result(uri, tags, duration, seekable, mime, have_audio)
        finally:
            signals.clear()
            pipeline.set_state(Gst.State.NULL)
            del pipeline


# Turns out it's _much_ faster to just create a new pipeline for every as
# decodebins and other elements don't seem to take well to being reused.
def _setup_pipeline(uri: str, proxy_config=None) -> tuple[Gst.Pipeline, utils.Signals]:
    src = Gst.Element.make_from_uri(Gst.URIType.SRC, uri)
    if not src:
        msg = f"GStreamer can not open: {uri}"
        raise exceptions.ScannerError(msg)

    if proxy_config:
        utils.setup_proxy(src, proxy_config)

    signals = utils.Signals()

    pipeline = Gst.ElementFactory.make("pipeline")
    if pipeline is None:
        msg = "Failed to create GStreamer pipeline element."
        raise exceptions.AudioException(msg)
    pipeline = cast(Gst.Pipeline, pipeline)
    pipeline.add(src)

    if _has_src_pads(src):
        _setup_decodebin(src, src.get_static_pad("src"), pipeline, signals)
    elif _has_dynamic_src_pad(src):
        signals.connect(src, "pad-added", _setup_decodebin, pipeline, signals)
    else:
        msg = "No pads found in source element."
        raise exceptions.ScannerError(msg)

    return pipeline, signals


def _has_src_pads(element) -> bool:
    pads = []
    element.iterate_src_pads().foreach(pads.append)
    return bool(pads)


def _has_dynamic_src_pad(element) -> bool:
    for template in element.get_pad_template_list():
        if (
            template.direction == Gst.PadDirection.SRC
            and template.presence == Gst.PadPresence.SOMETIMES
        ):
            return True
    return False


def _setup_decodebin(element, pad, pipeline, signals) -> None:  # noqa: ARG001
    typefind = Gst.ElementFactory.make("typefind")
    if typefind is None:
        msg = "Failed to create GStreamer typefind element."
        raise exceptions.AudioException(msg)

    decodebin = Gst.ElementFactory.make("decodebin")
    if decodebin is None:
        msg = "Failed to create GStreamer decodebin element."
        raise exceptions.AudioException(msg)

    for el in (typefind, decodebin):
        pipeline.add(el)
        el.sync_state_with_parent()

    pad.link(typefind.get_static_pad("sink"))
    typefind.link(decodebin)

    signals.connect(typefind, "have-type", _have_type, decodebin)
    signals.connect(decodebin, "pad-added", _pad_added, pipeline)
    signals.connect(decodebin, "autoplug-select", _autoplug_select)


def _have_type(
    element: Gst.Element,
    _probability: int,
    caps: Gst.Caps,
    decodebin: Gst.Bin,
) -> None:
    decodebin.set_property("sink-caps", caps)
    struct = Gst.Structure.new_empty("have-type")
    struct.set_value("caps", caps.get_structure(0))

    element_bus = element.get_bus()
    if element_bus is None:
        msg = "Failed to get bus of GStreamer element."
        raise exceptions.AudioException(msg)

    message = Gst.Message.new_application(element, struct)
    if message is None:
        msg = "Failed to create GStreamer message."
        raise exceptions.AudioException(msg)

    element_bus.post(message)


def _pad_added(
    element: Gst.Element,
    pad: Gst.Pad,
    pipeline: Gst.Pipeline,
) -> None:
    fakesink = Gst.ElementFactory.make("fakesink")
    if fakesink is None:
        msg = "Failed to create GStreamer fakesink element."
        raise exceptions.AudioException(msg)

    fakesink.set_property("sync", False)

    pipeline.add(fakesink)
    fakesink.sync_state_with_parent()
    fakesink_sink = fakesink.get_static_pad("sink")
    if fakesink_sink is None:
        msg = "Failed to get sink pad of GStreamer fakesink."
        raise exceptions.AudioException(msg)
    pad.link(fakesink_sink)

    raw_caps = Gst.Caps.from_string("audio/x-raw")
    assert raw_caps

    if pad.query_caps().is_subset(raw_caps):
        # Probably won't happen due to autoplug-select fix, but lets play it
        # safe until we've tested more.
        struct = Gst.Structure.new_empty("have-audio")

        element_bus = element.get_bus()
        if element_bus is None:
            msg = "Failed to get bus of GStreamer element."
            raise exceptions.AudioException(msg)

        message = Gst.Message.new_application(element, struct)
        if message is None:
            msg = "Failed to create GStreamer message."
            raise exceptions.AudioException(msg)

        element_bus.post(message)


def _autoplug_select(
    element: Gst.Element,
    _pad: Gst.Pad,
    _caps: Gst.Caps,
    factory: Gst.ElementFactory,
) -> GstAutoplugSelectResult:
    if factory.list_is_type(
        GstElementFactoryListType.DECODER | GstElementFactoryListType.AUDIO,
    ):
        struct = Gst.Structure.new_empty("have-audio")

        element_bus = element.get_bus()
        if element_bus is None:
            msg = "Failed to get bus of GStreamer element."
            raise exceptions.AudioException(msg)

        message = Gst.Message.new_application(element, struct)
        if message is None:
            msg = "Failed to create GStreamer message."
            raise exceptions.AudioException(msg)

        element_bus.post(message)

    if not factory.list_is_type(
        GstElementFactoryListType.DEMUXER
        | GstElementFactoryListType.DEPAYLOADER
        | GstElementFactoryListType.PARSER,
    ):
        return GstAutoplugSelectResult.EXPOSE
    return GstAutoplugSelectResult.TRY


def _start_pipeline(pipeline: Gst.Pipeline) -> None:
    result = pipeline.set_state(Gst.State.PAUSED)
    if result == Gst.StateChangeReturn.NO_PREROLL:
        pipeline.set_state(Gst.State.PLAYING)


def _query_duration(pipeline: Gst.Pipeline) -> tuple[bool, int | None]:
    success, duration = pipeline.query_duration(Gst.Format.TIME)
    if not success:
        duration = None  # Make sure error case preserves None.
    elif duration < 0:
        duration = None  # Stream without duration.
    else:
        duration = int(duration // Gst.MSECOND)
    return success, duration


def _query_seekable(pipeline: Gst.Pipeline) -> bool:
    query = Gst.Query.new_seeking(Gst.Format.TIME)
    pipeline.query(query)
    return query.parse_seeking()[1]


def _process(  # noqa: C901, PLR0911, PLR0912, PLR0915
    pipeline: Gst.Pipeline,
    timeout_ms: int,
) -> tuple[dict[str, Any], str | None, bool, int | None]:
    bus = pipeline.get_bus()
    tags = {}
    mime: str | None = None
    have_audio = False
    missing_message = None
    duration = None

    types = (
        Gst.MessageType.ELEMENT
        | Gst.MessageType.APPLICATION
        | Gst.MessageType.ERROR
        | Gst.MessageType.EOS
        | Gst.MessageType.ASYNC_DONE
        | Gst.MessageType.DURATION_CHANGED
        | Gst.MessageType.TAG
    )

    timeout = timeout_ms
    start = int(time.time() * 1000)
    while timeout > 0:
        msg = bus.timed_pop_filtered(timeout * Gst.MSECOND, types)
        if msg is None:
            break

        structure = msg.get_structure()

        if logger.isEnabledFor(log.TRACE_LOG_LEVEL) and structure:
            debug_text = structure.to_string()
            if len(debug_text) > 77:
                debug_text = debug_text[:77] + "..."
            _trace("element %s: %s", msg.src.get_name(), debug_text)

        if msg.type == Gst.MessageType.ELEMENT:
            if GstPbutils.is_missing_plugin_message(msg):
                missing_message = msg
        elif msg.type == Gst.MessageType.APPLICATION:
            if structure and structure.get_name() == "have-type":
                caps = cast(Gst.Caps | None, structure.get_value("caps"))
                if caps:
                    mime = cast(
                        str,
                        caps.get_name(),  # pyright: ignore[reportAttributeAccessIssue]
                    )
                    if mime.startswith("text/") or mime == "application/xml":
                        return tags, mime, have_audio, duration
            elif structure and structure.get_name() == "have-audio":
                have_audio = True
        elif msg.type == Gst.MessageType.ERROR:
            error, _debug = msg.parse_error()
            if (
                missing_message
                and not mime
                and (
                    (structure := missing_message.get_structure())
                    and (caps := structure.get_value("detail"))
                    and (mime := caps.get_structure(0).get_name())
                )
            ):
                return tags, mime, have_audio, duration
            raise exceptions.ScannerError(str(error))
        elif msg.type == Gst.MessageType.EOS:
            return tags, mime, have_audio, duration
        elif msg.type == Gst.MessageType.ASYNC_DONE:
            success, duration = _query_duration(pipeline)
            if tags and success:
                return tags, mime, have_audio, duration

            # Don't try workaround for non-seekable sources such as mmssrc:
            if not _query_seekable(pipeline):
                return tags, mime, have_audio, duration

            # Workaround for upstream bug which causes tags/duration to arrive
            # after pre-roll. We get around this by starting to play the track
            # and then waiting for a duration change.
            # https://bugzilla.gnome.org/show_bug.cgi?id=763553
            logger.debug("Using workaround for duration missing before play.")
            result = pipeline.set_state(Gst.State.PLAYING)
            if result == Gst.StateChangeReturn.FAILURE:
                return tags, mime, have_audio, duration

        elif msg.type == Gst.MessageType.DURATION_CHANGED and tags:
            # VBR formats sometimes seem to not have a duration by the time we
            # go back to paused. So just try to get it right away.
            success, duration = _query_duration(pipeline)
            pipeline.set_state(Gst.State.PAUSED)
            if success:
                return tags, mime, have_audio, duration
        elif msg.type == Gst.MessageType.TAG:
            taglist = msg.parse_tag()
            # Note that this will only keep the last tag.
            tags.update(tags_lib.convert_taglist(taglist))

        timeout = timeout_ms - (int(time.time() * 1000) - start)

    msg = f"Timeout after {timeout_ms:d}ms"
    raise exceptions.ScannerError(msg)


if __name__ == "__main__":
    import sys

    from mopidy.internal import path

    logging.basicConfig(
        format="%(asctime)-15s %(levelname)s %(message)s",
        level=log.TRACE_LOG_LEVEL,
    )

    scanner = Scanner(5000)
    for uri in sys.argv[1:]:
        if not Gst.uri_is_valid(uri):
            uri = path.path_to_uri(Path(uri).resolve())
        try:
            result = scanner.scan(uri)
            for key in ("uri", "mime", "duration", "playable", "seekable"):
                value = getattr(result, key)
                print(f"{key:<20}   {value}")  # noqa: T201
            print("tags")  # noqa: T201
            for tag, value in result.tags.items():
                line = f"{tag:<20}   {value}"
                if len(line) > 77:
                    line = line[:77] + "..."
                print(line)  # noqa: T201
        except exceptions.ScannerError as error:
            print(f"{uri}: {error}")  # noqa: T201
