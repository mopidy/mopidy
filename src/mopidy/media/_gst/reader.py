from __future__ import annotations

import dataclasses
import logging
import time
from typing import TYPE_CHECKING, override

from mopidy._lib.gi import GLib, Gst
from mopidy.media import EmbeddedImage, MediaInfo, MediaReaderError
from mopidy.media._api import MediaInfoReader
from mopidy.media._gst.pipeline import GstReaderPipeline
from mopidy.media._gst.tags import convert_tags_to_track
from mopidy.media._gst.types import (
    GstAsyncDone,
    GstBusMessage,
    GstDurationChanged,
    GstEndOfStream,
    GstError,
    GstHaveType,
    GstMissingPlugin,
    GstTag,
)
from mopidy.types import DurationMs

if TYPE_CHECKING:
    from mopidy._lib.gst import GstTags
    from mopidy.config import ProxyConfig
    from mopidy.models import Track
    from mopidy.types import Uri

logger = logging.getLogger(__name__)


class GstMediaInfoReader(MediaInfoReader):
    """Media info reader that uses GStreamer."""

    def __init__(self, *, proxy_config: ProxyConfig | None = None) -> None:
        self._proxy_config = proxy_config

    @override
    def read_media_info(self, uri: Uri, *, timeout: DurationMs) -> MediaInfo:
        result = GstRead(
            uri,
            timeout=timeout,
            proxy_config=self._proxy_config,
        ).run()
        return result.info


@dataclasses.dataclass(frozen=True)
class GstReadResult:
    """The result of one read of a URI."""

    info: MediaInfo

    # Only for the deprecated Scanner. Remove them together with it.
    legacy_scanner_tags: GstTags
    legacy_scanner_mime: str | None


class GstRead:
    """One read of a URI, driven by the bus messages of its pipeline.

    Args:
        uri: The URI to read.
        timeout: The timeout for the read.
        proxy_config: The proxy config to use for the read.
        pipeline: The pipeline to use. Only for tests.
    """

    def __init__(
        self,
        uri: Uri,
        *,
        timeout: DurationMs,
        proxy_config: ProxyConfig | None = None,
        pipeline: GstReaderPipeline | None = None,
    ) -> None:
        if pipeline is None:
            pipeline = GstReaderPipeline(uri, proxy_config=proxy_config)
        self._uri = uri
        self._timeout = timeout
        self._pipeline = pipeline
        self._tags: GstTags = {}
        self._mime: str | None = None
        self._playable = False
        self._duration: DurationMs | None = None
        self._missing_plugin_mime: str | None = None

    def run(self) -> GstReadResult:
        """Read the URI, until the read is done or until the timeout."""
        try:
            self._pipeline.start()
            return self._handle_messages()
        finally:
            self._pipeline.teardown()

    def _handle_messages(self) -> GstReadResult:
        remaining = self._timeout
        start = time.monotonic()
        while remaining > 0:
            message = self._pipeline.pop_message(remaining)
            if message is not None and self._on_message(message):
                return self._result()
            remaining = DurationMs(
                self._timeout - int((time.monotonic() - start) * 1000)
            )

        msg = f"Timeout after {self._timeout:d}ms"
        raise MediaReaderError(msg)

    def _on_message(self, message: GstBusMessage) -> bool:
        """Handle one bus message.

        Returns `True` when the read is done.
        """
        match message:
            case GstAsyncDone():
                return self._on_gst_async_done()
            case GstDurationChanged():
                return self._on_gst_duration_changed()
            case GstEndOfStream():
                return True
            case GstError(error, _debug):
                return self._on_gst_error(error)
            case GstHaveType(mime):
                return self._on_gst_have_type(mime)
            case GstMissingPlugin(mime):
                self._missing_plugin_mime = mime
            case GstTag(tags):
                # A later tag message replaces the values of the tags it has.
                self._tags.update(tags)
        return False

    def _on_gst_async_done(self) -> bool:
        success, self._duration = self._pipeline.query_duration()
        if self._tags and success:
            return True

        # Don't try workaround for non-seekable sources such as mmssrc:
        if not self._pipeline.query_seekable():
            return True

        # Workaround for upstream bug which causes tags/duration to arrive
        # after pre-roll. We get around this by starting to play the track
        # and then waiting for a duration change.
        # https://bugzilla.gnome.org/show_bug.cgi?id=763553
        logger.debug("Using workaround for duration missing before play.")
        return not self._pipeline.set_state(Gst.State.PLAYING)

    def _on_gst_duration_changed(self) -> bool:
        if not self._tags:
            return False

        # VBR formats sometimes seem to not have a duration by the time we
        # go back to paused. So just try to get it right away.
        success, self._duration = self._pipeline.query_duration()
        self._pipeline.set_state(Gst.State.PAUSED)
        return success

    def _on_gst_error(self, error: GLib.Error) -> bool:
        if self._missing_plugin_mime and not self._mime:
            self._mime = self._missing_plugin_mime
            return True
        raise MediaReaderError(str(error))

    def _on_gst_have_type(self, mime: str) -> bool:
        self._mime = mime
        if mime.startswith("audio/"):
            self._playable = True
        return mime.startswith("text/") or mime == "application/xml"

    def _result(self) -> GstReadResult:
        return GstReadResult(
            info=MediaInfo(
                track=self._track(),
                playable=self._playable,
                seekable=self._pipeline.query_seekable(),
                images=self._images(),
            ),
            legacy_scanner_tags=self._tags,
            legacy_scanner_mime=self._mime,
        )

    def _track(self) -> Track:
        """Convert the tags to a track, and leave out the tags that do not convert."""
        try:
            return self._convert_tags(self._tags)
        except MediaReaderError:
            pass

        # Add the tags one at a time, and keep each tag that still converts.
        valid_tags: GstTags = {}
        for tag, values in self._tags.items():
            try:
                self._convert_tags({**valid_tags, tag: values})
            except MediaReaderError as exc:
                logger.debug("Leaving out tag %r of %s: %s", tag, self._uri, exc)
            else:
                valid_tags[tag] = values
        return self._convert_tags(valid_tags)

    def _convert_tags(self, tags: GstTags) -> Track:
        return convert_tags_to_track(tags, uri=self._uri, length=self._duration)

    def _images(self) -> tuple[EmbeddedImage, ...]:
        """Get the images that are embedded in the tags."""
        return tuple(
            EmbeddedImage(data=value)
            for tag in (Gst.TAG_IMAGE, Gst.TAG_PREVIEW_IMAGE)
            for value in self._tags.get(tag, [])
            if isinstance(value, bytes)
        )
