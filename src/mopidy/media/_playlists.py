from __future__ import annotations

import configparser
import math
import re
import urllib.parse
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from mopidy.media._models import PlaylistEntry
from mopidy.models import Track
from mopidy.types import DurationMs, Uri

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    _Parser = Callable[[str, str], tuple[PlaylistEntry, ...] | None]

_XSPF_NS = "{http://xspf.org/ns/0/}"

# The characters that RFC 3986 allows in a URI, and the percent sign.
_URI_CHARS = ":/?#[]@!$&'()*+,;=-._~%"

# Control characters that do not occur in text, but often occur in media.
_BINARY_RE = re.compile(r"[\x00-\x08\x0e-\x1f]")


def parse_playlist_entries(
    data: bytes,
    *,
    base_uri: str,
    encoding: str = "utf-8",
    media_type: str | None = None,
    uri: str | None = None,
) -> tuple[PlaylistEntry, ...]:
    """Parse the playlist entries of a playlist document.

    The formats are M3U, with and without the `#EXTM3U` header, PLS, XSPF,
    ASX, ASX reference and URI list. The content decides the format.
    `media_type` and `uri` are only hints for which format to try first.

    HLS and DASH documents give no entries. Content that is not a playlist
    document also gives no entries.

    Args:
        data: The content of the playlist document.
        base_uri: The URI to join relative entries with.
        encoding: The encoding of `data`. Bytes that do not decode are
            replaced.
        media_type: The media type of the playlist document, such as the
            HTTP `Content-Type`.
        uri: The URI of the playlist document.

    Returns:
        The playlist entries, in the order of the playlist document.
    """
    text = data.decode(encoding, errors="replace").removeprefix("\ufeff")
    if _is_hls(text):
        return ()
    for parser in _parsers(media_type, uri):
        entries = parser(text, base_uri)
        if entries is not None:
            return entries
    return ()


def _parsers(media_type: str | None, uri: str | None) -> list[_Parser]:
    parsers: list[_Parser] = [
        _parse_m3u,
        _parse_pls,
        _parse_asx_reference,
        _parse_xspf,
        _parse_asx,
    ]
    hinted = [
        parser
        for hint in (_media_type_hint(media_type), _uri_hint(uri))
        for parser in _HINTS.get(hint or "", ())
    ]
    # The URI list has no header, so it goes last.
    return [*dict.fromkeys([*hinted, *parsers]), _parse_uri_list]


def is_playlist_media_type(media_type: str) -> bool:
    """Tell if a media type is the media type of a playlist format."""
    return "/" in media_type and media_type in _HINTS


def _media_type_hint(media_type: str | None) -> str | None:
    if media_type is None:
        return None
    return media_type.split(";", maxsplit=1)[0].strip().lower()


def _uri_hint(uri: str | None) -> str | None:
    if uri is None:
        return None
    return PurePosixPath(urllib.parse.urlsplit(uri).path).suffix.lower()


def _is_hls(text: str) -> bool:
    return any(line.lstrip().startswith("#EXT-X-") for line in text.splitlines())


def _parse_m3u(text: str, base_uri: str) -> tuple[PlaylistEntry, ...] | None:
    if text.lstrip()[:7].upper() != "#EXTM3U":
        return None
    return tuple(_parse_lines(text.splitlines(), base_uri, header=True))


def _parse_uri_list(text: str, base_uri: str) -> tuple[PlaylistEntry, ...] | None:
    # This is also M3U without the #EXTM3U header.
    if _BINARY_RE.search(text) or text.lstrip().startswith("<"):
        return None
    return tuple(_parse_lines(text.splitlines(), base_uri, header=False))


def _parse_lines(
    lines: Iterable[str],
    base_uri: str,
    *,
    header: bool,
) -> Iterable[PlaylistEntry]:
    name = length = None
    for line in (line.strip() for line in lines):
        if line.startswith("#EXTINF:"):
            info, _, name = line.removeprefix("#EXTINF:").partition(",")
            length = _seconds_to_duration(next(iter(info.split()), None))
            continue
        if not line or line.startswith("#"):
            continue
        if not header and not _is_uri_or_path(line):
            continue
        yield _entry([_join_path(base_uri, line)], name=name, length=length)
        name = length = None


def _is_uri_or_path(line: str) -> bool:
    if urllib.parse.urlsplit(line).scheme and not any(c.isspace() for c in line):
        return True
    return "/" in line or bool(PurePosixPath(line).suffix)


def _parse_pls(text: str, base_uri: str) -> tuple[PlaylistEntry, ...] | None:
    options = _ini_options(text, "playlist")
    if options is None:
        return None
    titles = dict(_numbered(options, "title"))
    lengths = dict(_numbered(options, "length"))
    entries = []
    for number, value in _numbered(options, "file"):
        if path := value.strip("\"'"):
            entries.append(
                _entry(
                    [_join_path(base_uri, path)],
                    name=titles.get(number),
                    length=_seconds_to_duration(lengths.get(number)),
                )
            )
    return tuple(entries)


def _parse_asx_reference(
    text: str,
    base_uri: str,
) -> tuple[PlaylistEntry, ...] | None:
    options = _ini_options(text, "reference")
    if options is None:
        return None
    return tuple(
        _entry([_join_path(base_uri, path)])
        for _number, value in _numbered(options, "ref")
        if (path := value.strip("\"'"))
    )


def _ini_options(text: str, section: str) -> dict[str, str] | None:
    if not text.lstrip().lower().startswith(f"[{section}]"):
        return None
    parser = configparser.RawConfigParser(strict=False)
    try:
        parser.read_string(text)
    except configparser.Error:
        return {}
    options: dict[str, str] = {}
    for name in parser.sections():
        if name.lower() == section:
            options.update(parser.items(name))
    return options


def _numbered(options: dict[str, str], prefix: str) -> list[tuple[int, str]]:
    # Ignore NumberOfEntries. It is often not correct.
    return sorted(
        (int(key.removeprefix(prefix)), value)
        for key, value in options.items()
        if key.startswith(prefix) and key.removeprefix(prefix).isdigit()
    )


def _parse_xspf(text: str, base_uri: str) -> tuple[PlaylistEntry, ...] | None:
    root = _xml_root(text)
    if root is None or root.tag != f"{_XSPF_NS}playlist":
        return None
    entries = []
    for track in root.iterfind(f"{_XSPF_NS}tracklist/{_XSPF_NS}track"):
        alternatives = [
            urllib.parse.urljoin(base_uri, location.text.strip())
            for location in track.iterfind(f"{_XSPF_NS}location")
            if location.text and location.text.strip()
        ]
        if alternatives:
            entries.append(
                _entry(
                    alternatives,
                    name=track.findtext(f"{_XSPF_NS}title"),
                    length=_milliseconds_to_duration(
                        track.findtext(f"{_XSPF_NS}duration")
                    ),
                )
            )
    return tuple(entries)


def _parse_asx(text: str, base_uri: str) -> tuple[PlaylistEntry, ...] | None:
    root = _xml_root(text)
    if root is None or root.tag != "asx":
        return None
    entries = []
    for element in root:
        if element.tag == "entry":
            hrefs = [ref.get("href", "") for ref in element.iterfind("ref")]
            # Some servers put an href on the entry.
            hrefs.append(element.get("href", ""))
        elif element.tag == "entryref":
            # A nested ASX document.
            hrefs = [element.get("href", "")]
        else:
            continue
        alternatives = [
            urllib.parse.urljoin(base_uri, href.strip())
            for href in hrefs
            if href.strip()
        ]
        if alternatives:
            entries.append(
                _entry(
                    alternatives,
                    name=element.findtext("title"),
                    length=_asx_duration(element.find("duration")),
                )
            )
    return tuple(entries)


def _xml_root(text: str) -> ET.Element | None:
    if not text.lstrip().startswith("<"):
        return None
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None
    # ASX element and attribute names are not case sensitive.
    for element in root.iter():
        element.tag = element.tag.lower()
        element.attrib = {key.lower(): value for key, value in element.items()}
    return root


def _asx_duration(element: ET.Element | None) -> DurationMs | None:
    # The format is [[hh:]mm:]ss[.fract].
    if element is None:
        return None
    seconds = 0.0
    try:
        for part in element.get("value", "").split(":"):
            seconds = seconds * 60 + float(part)
    except ValueError:
        return None
    return _duration(seconds * 1000)


def _seconds_to_duration(value: str | None) -> DurationMs | None:
    try:
        return _duration(float(value or "") * 1000)
    except ValueError:
        return None


def _milliseconds_to_duration(value: str | None) -> DurationMs | None:
    try:
        return _duration(float(value or ""))
    except ValueError:
        return None


def _duration(milliseconds: float) -> DurationMs | None:
    # Zero and negative lengths, such as -1, mean that the length is unknown.
    if not math.isfinite(milliseconds) or milliseconds <= 0:
        return None
    return DurationMs(round(milliseconds))


def _join_path(base_uri: str, path: str) -> str:
    # Entries in M3U, PLS and ASX reference documents are URIs or file paths.
    if urllib.parse.urlsplit(path).scheme:
        return path
    # In a local playlist document, all characters are part of the file name.
    safe = "/" if urllib.parse.urlsplit(base_uri).scheme == "file" else _URI_CHARS
    return urllib.parse.urljoin(base_uri, urllib.parse.quote(path, safe=safe))


def _entry(
    alternatives: list[str],
    *,
    name: str | None = None,
    length: DurationMs | None = None,
) -> PlaylistEntry:
    uris = tuple(Uri(alternative) for alternative in alternatives)
    return PlaylistEntry(
        track=Track(uri=uris[0], name=(name or "").strip() or None, length=length),
        alternatives=uris,
    )


_ASX = (_parse_asx, _parse_asx_reference)
_M3U = (_parse_m3u,)
_PLS = (_parse_pls,)
_XSPF = (_parse_xspf,)

_HINTS: dict[str, tuple[_Parser, ...]] = {
    ".asx": _ASX,
    ".wax": _ASX,
    ".wvx": _ASX,
    ".wmx": _ASX,
    ".m3u": _M3U,
    ".m3u8": _M3U,
    ".pls": _PLS,
    ".xspf": _XSPF,
    "application/vnd.apple.mpegurl": _M3U,
    "application/x-mpegurl": _M3U,
    "application/xspf+xml": _XSPF,
    "audio/mpegurl": _M3U,
    "audio/x-mpegurl": _M3U,
    "audio/x-ms-asx": _ASX,
    "audio/x-ms-wax": _ASX,
    "audio/x-scpls": _PLS,
    "video/x-ms-asf": _ASX,
    "video/x-ms-wvx": _ASX,
}
