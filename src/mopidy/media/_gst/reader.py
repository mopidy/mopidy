from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, override

from mopidy import exceptions
from mopidy._lib.gi import GLib, Gst
from mopidy.media._api import MediaInfoReader, MediaReadError
from mopidy.media._gst.pipeline import read_media_data
from mopidy.media._gst.tags import convert_tags_to_track
from mopidy.media._models import EmbeddedImage, MediaInfo

if TYPE_CHECKING:
    from mopidy.config import ProxyConfig
    from mopidy.models import Track
    from mopidy.types import DurationMs, Uri

logger = logging.getLogger(__name__)


class GstMediaInfoReader(MediaInfoReader):
    """Media info reader that uses GStreamer."""

    def __init__(self, *, proxy_config: ProxyConfig | None = None) -> None:
        self._proxy_config = proxy_config

    @override
    def read_media_info(self, uri: Uri, *, timeout: DurationMs) -> MediaInfo:
        try:
            data = read_media_data(
                uri,
                timeout_ms=timeout,
                proxy_config=self._proxy_config,
            )
        except (exceptions.ScannerError, GLib.Error) as exc:
            raise MediaReadError(str(exc)) from exc
        return MediaInfo(
            track=_convert_valid_tags(data.tags, uri=uri, length=data.duration),
            playable=data.playable,
            seekable=data.seekable,
            images=_embedded_images(data.tags),
        )


def _convert_valid_tags(
    tags: dict[str, Any],
    *,
    uri: Uri,
    length: DurationMs | None,
) -> Track:
    try:
        return convert_tags_to_track(tags, uri=uri, length=length)
    except exceptions.ScannerError:
        pass

    # Add the tags one at a time, and keep each tag that still converts.
    valid_tags: dict[str, Any] = {}
    for tag, values in tags.items():
        try:
            convert_tags_to_track({**valid_tags, tag: values}, uri=uri, length=length)
        except exceptions.ScannerError as exc:
            logger.debug("Leaving out tag %r of %s: %s", tag, uri, exc)
        else:
            valid_tags[tag] = values
    return convert_tags_to_track(valid_tags, uri=uri, length=length)


def _embedded_images(tags: dict[str, Any]) -> tuple[EmbeddedImage, ...]:
    return tuple(
        EmbeddedImage(data=value)
        for tag in (Gst.TAG_IMAGE, Gst.TAG_PREVIEW_IMAGE)
        for value in tags.get(tag, [])
        if isinstance(value, bytes)
    )
