from __future__ import annotations

import dataclasses
import logging
import time
from typing import TYPE_CHECKING, Any, cast

from mopidy._lib import logs
from mopidy._lib.gi import Gst, GstPbutils
from mopidy._lib.gst import (
    Signals,
    from_gst_taglist,
    from_gst_time,
    setup_proxy,
    to_gst_time,
)
from mopidy.media import MediaReaderError
from mopidy.types import DurationMs

if TYPE_CHECKING:
    from mopidy._lib.gst import GstTags
    from mopidy.config import ProxyConfig


@dataclasses.dataclass(frozen=True)
class GstMediaData:
    tags: GstTags
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
    timeout: DurationMs,
    proxy_config: ProxyConfig | None = None,
) -> GstMediaData:
    pipeline = GstReaderPipeline(uri, proxy_config=proxy_config)

    try:
        pipeline.start()
        tags, mime, playable, duration = _process(pipeline, timeout)
        seekable = pipeline.query_seekable()
        return GstMediaData(tags, duration, seekable, mime, playable)
    finally:
        pipeline.teardown()


_MESSAGE_TYPES = (
    Gst.MessageType.ELEMENT
    | Gst.MessageType.APPLICATION
    | Gst.MessageType.ERROR
    | Gst.MessageType.EOS
    | Gst.MessageType.ASYNC_DONE
    | Gst.MessageType.DURATION_CHANGED
    | Gst.MessageType.TAG
)


class GstReaderPipeline:
    """The GStreamer element graph used to read the media of one URI.

    Make a new pipeline for each read. It is much faster than to reuse one, as
    parsebin and other elements do not work well when reused.
    """

    def __init__(
        self,
        uri: str,
        *,
        proxy_config: ProxyConfig | None = None,
    ) -> None:
        self._signals = Signals()
        self._pipeline = self._make_pipeline()
        self._add_source(uri, proxy_config)

    def _make_pipeline(self) -> Gst.Pipeline:
        pipeline = Gst.ElementFactory.make("pipeline")
        if pipeline is None:
            msg = "Failed to create GStreamer pipeline element."
            raise MediaReaderError(msg)
        return cast(Gst.Pipeline, pipeline)

    def _add_source(self, uri: str, proxy_config: ProxyConfig | None) -> None:
        src = Gst.Element.make_from_uri(Gst.URIType.SRC, uri)
        if not src:
            msg = f"GStreamer can not open: {uri}"
            raise MediaReaderError(msg)

        if proxy_config:
            setup_proxy(src, proxy_config)

        self._pipeline.add(src)

        if static_src_pad := src.get_static_pad("src"):
            self._add_parsebin(static_src_pad)
        elif _has_dynamic_src_pad(src):
            self._signals.connect(src, "pad-added", self._on_src_pad_added)
        else:
            msg = "No pads found in source element."
            raise MediaReaderError(msg)

    def _on_src_pad_added(self, _src: Gst.Element, pad: Gst.Pad) -> None:
        self._add_parsebin(pad)

    def _add_parsebin(self, pad: Gst.Pad) -> None:
        if (parsebin := Gst.ElementFactory.make("parsebin")) is None:
            msg = "Failed to create GStreamer parsebin element."
            raise MediaReaderError(msg)

        self._pipeline.add(parsebin)
        parsebin.sync_state_with_parent()

        if (sink_pad := parsebin.get_static_pad("sink")) is None:
            msg = "Failed to get sink pad of GStreamer parsebin element."
            raise MediaReaderError(msg)

        pad.link(sink_pad)

        self._signals.connect(parsebin, "pad-added", self._on_parsebin_pad_added)

    def _on_parsebin_pad_added(self, parsebin: Gst.Element, pad: Gst.Pad) -> None:
        pad_caps = pad.get_current_caps() or pad.query_caps()

        if (bus := parsebin.get_bus()) is None:
            msg = "Failed to get bus of GStreamer element."
            raise MediaReaderError(msg)

        if pad_caps is not None and pad_caps.get_size() > 0:
            have_type = Gst.Structure.new_empty("have-type")
            have_type.set_value("mime", _get_structure_name(pad_caps.get_structure(0)))
            bus.post(Gst.Message.new_application(parsebin, have_type))

        if (fakesink := Gst.ElementFactory.make("fakesink")) is None:
            msg = "Failed to create GStreamer fakesink element."
            raise MediaReaderError(msg)

        fakesink.set_property("sync", False)

        self._pipeline.add(fakesink)
        fakesink.sync_state_with_parent()

        if (fakesink_sink := fakesink.get_static_pad("sink")) is None:
            msg = "Failed to get sink pad of GStreamer fakesink."
            raise MediaReaderError(msg)

        pad.link(fakesink_sink)

    def start(self) -> None:
        """Start the pipeline, so that it reads the media."""
        result = self._pipeline.set_state(Gst.State.PAUSED)
        if result == Gst.StateChangeReturn.NO_PREROLL:
            self._pipeline.set_state(Gst.State.PLAYING)

    def set_state(self, state: Gst.State) -> bool:
        """Set the state of the pipeline.

        Returns `True` if successful, else `False`.
        """
        result = self._pipeline.set_state(state)
        return result != Gst.StateChangeReturn.FAILURE

    def pop_message(self, timeout: DurationMs) -> Gst.Message | None:
        """Wait for the next bus message that the reader uses.

        Returns `None` if no message arrives before the timeout.
        """
        if (bus := self._pipeline.get_bus()) is None:
            return None
        return bus.timed_pop_filtered(to_gst_time(timeout), _MESSAGE_TYPES)

    def query_duration(self) -> tuple[bool, DurationMs | None]:
        """Get the duration of the media in milliseconds.

        Returns if the query was successful, and the duration. The duration is
        `None` if the query failed or if the media has no duration.
        """
        success, duration = self._pipeline.query_duration(Gst.Format.TIME)
        if not success:
            duration = None  # Make sure error case preserves None.
        elif duration < 0:
            duration = None  # Stream without duration.
        else:
            duration = from_gst_time(duration)
        return success, duration

    def query_seekable(self) -> bool:
        """Check if the media allows seeking."""
        query = Gst.Query.new_seeking(Gst.Format.TIME)
        self._pipeline.query(query)
        return query.parse_seeking()[1]

    def teardown(self) -> None:
        self._signals.clear()
        self._pipeline.set_state(Gst.State.NULL)


def _has_dynamic_src_pad(element: Gst.Element) -> bool:
    for template in element.get_pad_template_list():
        if (
            template.direction == Gst.PadDirection.SRC
            and template.presence == Gst.PadPresence.SOMETIMES
        ):
            return True
    return False


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


def _process(  # noqa: C901, PLR0911, PLR0912
    pipeline: GstReaderPipeline,
    timeout: DurationMs,
) -> tuple[GstTags, str | None, bool, DurationMs | None]:
    tags: GstTags = {}
    mime: str | None = None
    playable = False
    missing_message = None
    duration = None

    remaining = timeout
    start = time.monotonic()
    while remaining > 0:
        if (msg := pipeline.pop_message(remaining)) is None:
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
                mime = cast(str, structure.get_value("mime"))
                if mime.startswith("audio/"):
                    playable = True
                if mime.startswith("text/") or mime == "application/xml":
                    return tags, mime, playable, duration

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
            raise MediaReaderError(str(error))

        elif msg.type == Gst.MessageType.EOS:
            return tags, mime, playable, duration

        elif msg.type == Gst.MessageType.ASYNC_DONE:
            success, duration = pipeline.query_duration()
            if tags and success:
                return tags, mime, playable, duration

            # Don't try workaround for non-seekable sources such as mmssrc:
            if not pipeline.query_seekable():
                return tags, mime, playable, duration

            # Workaround for upstream bug which causes tags/duration to arrive
            # after pre-roll. We get around this by starting to play the track
            # and then waiting for a duration change.
            # https://bugzilla.gnome.org/show_bug.cgi?id=763553
            logger.debug("Using workaround for duration missing before play.")
            if not pipeline.set_state(Gst.State.PLAYING):
                return tags, mime, playable, duration

        elif msg.type == Gst.MessageType.DURATION_CHANGED and tags:
            # VBR formats sometimes seem to not have a duration by the time we
            # go back to paused. So just try to get it right away.
            success, duration = pipeline.query_duration()
            pipeline.set_state(Gst.State.PAUSED)
            if success:
                return tags, mime, playable, duration

        elif msg.type == Gst.MessageType.TAG:
            taglist = msg.parse_tag()
            # Note that this will only keep the last tag.
            tags.update(from_gst_taglist(taglist))

        remaining = DurationMs(timeout - int((time.monotonic() - start) * 1000))

    msg = f"Timeout after {timeout:d}ms"
    raise MediaReaderError(msg)
