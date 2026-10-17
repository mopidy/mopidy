from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from mopidy._lib import logs
from mopidy._lib.gi import GLib, Gst, GstPbutils
from mopidy._lib.gst import (
    Signals,
    from_gst_taglist,
    from_gst_time,
    setup_proxy,
    to_gst_time,
)
from mopidy.media import MediaReaderError
from mopidy.media._gst.types import (
    GstAsyncDone,
    GstBusMessage,
    GstDurationChanged,
    GstEndOfStream,
    GstError,
    GstMissingPlugin,
    GstStreamFound,
    GstTag,
)

if TYPE_CHECKING:
    from mopidy.config import ProxyConfig
    from mopidy.types import DurationMs, Uri


logger = logging.getLogger(__name__)


def _trace(*args: Any, **kwargs: Any) -> None:
    logger.log(logs.TRACE_LOG_LEVEL, *args, **kwargs)


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
        uri: Uri,
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

    def _add_source(self, uri: Uri, proxy_config: ProxyConfig | None) -> None:
        try:
            src = Gst.Element.make_from_uri(Gst.URIType.SRC, uri)
        except GLib.Error as exc:
            raise MediaReaderError(str(exc)) from exc
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

    def _on_src_pad_added(self, src: Gst.Element, pad: Gst.Pad) -> None:
        # Runs on a GStreamer thread, so errors go on the bus.
        try:
            self._add_parsebin(pad)
        except MediaReaderError as exc:
            _post_error(src, str(exc))

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
        # Runs on a GStreamer thread, so errors go on the bus.
        pad_caps = pad.get_current_caps() or pad.query_caps()
        if pad_caps is not None and pad_caps.get_size() > 0:
            structure = Gst.Structure.new_empty("mopidy-stream-found")
            structure.set_value("mime", _get_structure_name(pad_caps.get_structure(0)))
            parsebin.post_message(Gst.Message.new_application(parsebin, structure))

        try:
            self._add_fakesink(pad)
        except MediaReaderError as exc:
            _post_error(parsebin, str(exc))

    def _add_fakesink(self, pad: Gst.Pad) -> None:
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

    def pop_message(self, timeout: DurationMs) -> GstBusMessage | None:
        """Wait for the next bus message and decode it.

        Returns `None` if no message arrives before the timeout, or if the
        reader does not use the message.
        """
        if (bus := self._pipeline.get_bus()) is None:
            return None
        if (
            message := bus.timed_pop_filtered(to_gst_time(timeout), _MESSAGE_TYPES)
        ) is None:
            return None
        return self._decode_bus_message(message)

    def _decode_bus_message(  # noqa: PLR0911
        self,
        message: Gst.Message,
    ) -> GstBusMessage | None:
        """Turn a bus message into one of our records, or drop it."""
        structure = message.get_structure()

        if logger.isEnabledFor(logs.TRACE_LOG_LEVEL) and structure is not None:
            debug_text = structure.to_string()
            if len(debug_text) > 77:
                debug_text = debug_text[:77] + "..."
            _trace("element %s: %s", message.src.get_name(), debug_text)

        match message.type:
            case Gst.MessageType.APPLICATION if (
                structure is not None
                and _get_structure_name(structure) == "mopidy-stream-found"
            ):
                return GstStreamFound(cast(str, structure.get_value("mime")))
            case Gst.MessageType.ASYNC_DONE:
                return GstAsyncDone()
            case Gst.MessageType.DURATION_CHANGED:
                return GstDurationChanged()
            case Gst.MessageType.EOS:
                return GstEndOfStream()
            case Gst.MessageType.ERROR:
                return GstError(*message.parse_error())
            case Gst.MessageType.ELEMENT if GstPbutils.is_missing_plugin_message(
                message
            ):
                return GstMissingPlugin(_missing_plugin_mime(structure))
            case Gst.MessageType.TAG:
                return GstTag(from_gst_taglist(message.parse_tag()))
            case _:
                return None

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
        self._signals.disconnect_all()
        self._pipeline.set_state(Gst.State.NULL)


def _post_error(element: Gst.Element, text: str) -> None:
    error = GLib.Error.new_literal(Gst.CoreError.quark(), text, Gst.CoreError.FAILED)
    element.post_message(Gst.Message.new_error(element, error, ""))


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


def _missing_plugin_mime(structure: Gst.Structure | None) -> str | None:
    if structure is None or (caps := structure.get_value("detail")) is None:
        return None
    return _get_structure_name(caps.get_structure(0))
