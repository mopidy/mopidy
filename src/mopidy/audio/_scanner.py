"""The scanner API.

A scanner reads metadata from a URI without playing it. This is separate
from the playback API in `mopidy.audio._api`: a scanner is an ordinary
object, not an actor, and it holds no state between calls.
"""

from __future__ import annotations

import enum

from mopidy.models import Track  # noqa: TC001
from mopidy.models._base import BaseModel
from mopidy.types import DurationMs, Uri  # noqa: TC001


class MediaKind(enum.StrEnum):
    """What kind of media a scanner believes it found.

    Mopidy plays the audio of a video container, so there is no separate
    value for video: such media is `AUDIO`.
    """

    AUDIO = "audio"
    """Media to play."""

    PLAYLIST = "playlist"
    """A list of other URIs, which has to be unwrapped before playing."""

    OTHER = "other"
    """Something Mopidy has no use for, such as an image or a text file."""


class ScanImageData(BaseModel):
    """An image embedded in scanned media.

    Unlike [Image][mopidy.models.Image], which points at an image with a URI,
    this carries the bytes the scanner read out of the media itself.
    """

    data: bytes
    """The raw image data."""


class ScanResult(BaseModel):
    """What a scanner found at a URI."""

    uri: Uri
    """The URI that was scanned."""

    track: Track
    """The metadata as a track. The duration is `track.length`."""

    kind: MediaKind = MediaKind.OTHER
    """What the scanner believes the media is.

    This is what callers should branch on. It is a belief, not a promise:
    scanners recognise playlists by a partial set of signals, so a caller
    that parses playlists itself may still find one in media reported as
    `OTHER`.
    """

    media_type: str | None = None
    """The media type of the scanned media, such as `audio/mpeg`.

    The raw answer the scanner got, where `kind` is what it made of it.
    Scanners built on something other than GStreamer may not report one.
    """

    playable: bool = False
    """Whether the scanner got as far as decoding audio.

    `kind` can be `AUDIO` while this is false, for media the scanner
    recognised but could not decode, such as a format with no plugin
    installed.
    """

    seekable: bool = False
    """Whether the media can be seeked in."""

    images: tuple[ScanImageData, ...] = ()
    """Images embedded in the media, such as cover art."""


class Scanner:
    """Scanner API.

    A scanner reads metadata from a URI without playing it. Get one from
    [create_scanner][mopidy.audio.create_scanner] rather than building an
    implementation yourself, so that the choice of implementation stays in
    one place.
    """

    def scan(self, uri: Uri, timeout: DurationMs | None = None) -> ScanResult:
        """Scan the given URI, collecting relevant metadata.

        Args:
            uri: URI of the resource to scan.
            timeout: Timeout for scanning in milliseconds. Defaults to the
                timeout the scanner was created with.

        Metadata that can't be coerced into a [Track][mopidy.models.Track] is
        left out, so a single bad tag does not fail the scan.

        Raises:
            mopidy.exceptions.ScannerError: If the URI can't be opened or if
                scanning times out.
        """
        raise NotImplementedError
