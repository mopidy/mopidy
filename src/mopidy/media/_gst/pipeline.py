from __future__ import annotations

import dataclasses
import logging
import time
from typing import TYPE_CHECKING, Any, cast

from mopidy import exceptions
from mopidy._lib import logs
from mopidy._lib.gi import Gst, GstPbutils
from mopidy._lib.gst import Signals, convert_taglist, setup_proxy
from mopidy.types import DurationMs

if TYPE_CHECKING:
    from mopidy.config import ProxyConfig


@dataclasses.dataclass(frozen=True)
class GstMediaData:
    tags: dict[str, Any]
    duration: DurationMs | None
    seekable: bool
    mime: str | None
    playable: bool


logger = logging.getLogger(__name__)


def _trace(*args: Any, **kwargs: Any) -> None:
    logger.log(logs.TRACE_LOG_LEVEL, *args, **kwargs)


def read_media_data(
    uri: str,
    *,
    timeout_ms: int,
    proxy_config: ProxyConfig | None = None,
) -> GstMediaData:
    pipeline, signals = _setup_pipeline(uri, proxy_config)

    try:
        _start_pipeline(pipeline)
        tags, mime, playable, duration = _process(pipeline, timeout_ms)
        seekable = _query_seekable(pipeline)
        return GstMediaData(tags, duration, seekable, mime, playable)
    finally:
        signals.clear()
        pipeline.set_state(Gst.State.NULL)
        del pipeline


# Turns out it's _much_ faster to just create a new pipeline for every as
# decodebins and other elements don't seem to take well to being reused.
def _setup_pipeline(
    uri: str,
    proxy_config: ProxyConfig | None = None,
) -> tuple[Gst.Pipeline, Signals]:
    src = Gst.Element.make_from_uri(Gst.URIType.SRC, uri)
    if not src:
        msg = f"GStreamer can not open: {uri}"
        raise exceptions.ScannerError(msg)

    if proxy_config:
        setup_proxy(src, proxy_config)

    signals = Signals()

    pipeline = Gst.ElementFactory.make("pipeline")
    if pipeline is None:
        msg = "Failed to create GStreamer pipeline element."
        raise exceptions.AudioException(msg)
    pipeline = cast(Gst.Pipeline, pipeline)
    pipeline.add(src)

    if static_src_pad := src.get_static_pad("src"):
        _setup_parsebin(src, static_src_pad, pipeline, signals)
    elif _has_dynamic_src_pad(src):
        signals.connect(src, "pad-added", _setup_parsebin, pipeline, signals)
    else:
        msg = "No pads found in source element."
        raise exceptions.ScannerError(msg)

    return pipeline, signals


def _has_dynamic_src_pad(element: Gst.Element) -> bool:
    for template in element.get_pad_template_list():
        if (
            template.direction == Gst.PadDirection.SRC
            and template.presence == Gst.PadPresence.SOMETIMES
        ):
            return True
    return False


def _setup_parsebin(
    element: Gst.Element,  # noqa: ARG001
    pad: Gst.Pad,
    pipeline: Gst.Pipeline,
    signals: Signals,
) -> None:
    if (parsebin := Gst.ElementFactory.make("parsebin")) is None:
        msg = "Failed to create GStreamer parsebin element."
        raise exceptions.AudioException(msg)

    pipeline.add(parsebin)
    parsebin.sync_state_with_parent()

    if (sink_pad := parsebin.get_static_pad("sink")) is None:
        msg = "Failed to get sink pad of GStreamer parsebin element."
        raise exceptions.AudioException(msg)

    pad.link(sink_pad)

    signals.connect(parsebin, "pad-added", _pad_added, pipeline)


def _pad_added(
    element: Gst.Element,
    pad: Gst.Pad,
    pipeline: Gst.Pipeline,
) -> None:
    pad_caps = pad.get_current_caps() or pad.query_caps()

    if (element_bus := element.get_bus()) is None:
        msg = "Failed to get bus of GStreamer element."
        raise exceptions.AudioException(msg)

    if pad_caps is not None and pad_caps.get_size() > 0:
        struct = pad_caps.get_structure(0)

        have_type = Gst.Structure.new_empty("have-type")
        have_type.set_value("caps", struct)
        element_bus.post(Gst.Message.new_application(element, have_type))

        if _get_structure_name(struct).startswith("audio/"):
            have_audio = Gst.Structure.new_empty("have-audio")
            element_bus.post(Gst.Message.new_application(element, have_audio))

    if (fakesink := Gst.ElementFactory.make("fakesink")) is None:
        msg = "Failed to create GStreamer fakesink element."
        raise exceptions.AudioException(msg)

    fakesink.set_property("sync", False)

    pipeline.add(fakesink)
    fakesink.sync_state_with_parent()

    if (fakesink_sink := fakesink.get_static_pad("sink")) is None:
        msg = "Failed to get sink pad of GStreamer fakesink."
        raise exceptions.AudioException(msg)

    pad.link(fakesink_sink)


def _start_pipeline(pipeline: Gst.Pipeline) -> None:
    result = pipeline.set_state(Gst.State.PAUSED)
    if result == Gst.StateChangeReturn.NO_PREROLL:
        pipeline.set_state(Gst.State.PLAYING)


def _query_duration(pipeline: Gst.Pipeline) -> tuple[bool, DurationMs | None]:
    success, duration = pipeline.query_duration(Gst.Format.TIME)
    if not success:
        duration = None  # Make sure error case preserves None.
    elif duration < 0:
        duration = None  # Stream without duration.
    else:
        duration = DurationMs(int(duration // Gst.MSECOND))
    return success, duration


def _query_seekable(pipeline: Gst.Pipeline) -> bool:
    query = Gst.Query.new_seeking(Gst.Format.TIME)
    pipeline.query(query)
    return query.parse_seeking()[1]


def _get_structure_name(struct: Gst.Structure) -> str:
    # GStreamer 1.25.0 to 1.26.2 (inclusive) broke the accessing
    # `caps.get_structure(0).get_name()`, but allow wrapping the
    # object in a context manager. With GStreamer 1.24.x one can
    # not use the structure as a context manager at all. Fixed in
    # version 1.26.3 where both methods are supported.
    try:
        return struct.get_name()
    except AttributeError:
        with struct as _struct:  # type: ignore[reportGeneralTypeIssues]
            return _struct.get_name()


def _process(  # noqa: C901, PLR0911, PLR0912, PLR0915
    pipeline: Gst.Pipeline,
    timeout_ms: int,
) -> tuple[dict[str, Any], str | None, bool, DurationMs | None]:
    bus = pipeline.get_bus()
    tags = {}
    mime: str | None = None
    playable = False
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
        if (msg := bus.timed_pop_filtered(timeout * Gst.MSECOND, types)) is None:
            break

        structure = msg.get_structure()

        if logger.isEnabledFor(logs.TRACE_LOG_LEVEL) and structure is not None:
            debug_text = structure.to_string()
            if len(debug_text) > 77:
                debug_text = debug_text[:77] + "..."
            _trace("element %s: %s", msg.src.get_name(), debug_text)

        if msg.type == Gst.MessageType.ELEMENT:
            if GstPbutils.is_missing_plugin_message(msg):
                missing_message = msg

        elif msg.type == Gst.MessageType.APPLICATION:
            if structure is not None and _get_structure_name(structure) == "have-type":
                caps = cast(Gst.Structure | None, structure.get_value("caps"))
                if caps is not None:
                    mime = _get_structure_name(caps)
                    if mime.startswith("text/") or mime == "application/xml":
                        return tags, mime, playable, duration
            elif structure is not None and structure.get_name() == "have-audio":
                playable = True

        elif msg.type == Gst.MessageType.ERROR:
            error, _debug = msg.parse_error()
            if (
                missing_message
                and not mime
                and (
                    ((structure := missing_message.get_structure()) is not None)
                    and ((caps := structure.get_value("detail")) is not None)
                    and (mime := _get_structure_name(caps.get_structure(0)))
                )
            ):
                return tags, mime, playable, duration
            raise exceptions.ScannerError(str(error))

        elif msg.type == Gst.MessageType.EOS:
            return tags, mime, playable, duration

        elif msg.type == Gst.MessageType.ASYNC_DONE:
            success, duration = _query_duration(pipeline)
            if tags and success:
                return tags, mime, playable, duration

            # Don't try workaround for non-seekable sources such as mmssrc:
            if not _query_seekable(pipeline):
                return tags, mime, playable, duration

            # Workaround for upstream bug which causes tags/duration to arrive
            # after pre-roll. We get around this by starting to play the track
            # and then waiting for a duration change.
            # https://bugzilla.gnome.org/show_bug.cgi?id=763553
            logger.debug("Using workaround for duration missing before play.")
            result = pipeline.set_state(Gst.State.PLAYING)
            if result == Gst.StateChangeReturn.FAILURE:
                return tags, mime, playable, duration

        elif msg.type == Gst.MessageType.DURATION_CHANGED and tags:
            # VBR formats sometimes seem to not have a duration by the time we
            # go back to paused. So just try to get it right away.
            success, duration = _query_duration(pipeline)
            pipeline.set_state(Gst.State.PAUSED)
            if success:
                return tags, mime, playable, duration

        elif msg.type == Gst.MessageType.TAG:
            taglist = msg.parse_tag()
            # Note that this will only keep the last tag.
            tags.update(convert_taglist(taglist))

        timeout = timeout_ms - (int(time.time() * 1000) - start)

    msg = f"Timeout after {timeout_ms:d}ms"
    raise exceptions.ScannerError(msg)
