"""Parser for CUE sheets.

A CUE sheet describes how one or more audio files are split into tracks. This
module only parses the text and finds the audio files. It does not read audio.
It only uses the standard library.
"""

from __future__ import annotations

import codecs
import dataclasses
import logging
import pathlib
import re
from collections.abc import Sequence

logger = logging.getLogger(__name__)

DEFAULT_ENCODINGS = ("utf-8", "cp1252")
"""The encodings tried, in order, for a CUE sheet that is not Unicode."""

# Used when the audio file named in a CUE sheet is missing, and a file with the
# same name and another extension is a more likely candidate. It is common that
# a sheet says `.wav` for a file that was later compressed to `.flac`.
AUDIO_EXTENSIONS = (
    ".flac",
    ".wv",
    ".ape",
    ".wav",
    ".tta",
    ".tak",
    ".m4a",
    ".ogg",
    ".opus",
    ".mp3",
)

_FRAMES_PER_SECOND = 75
_BOMS = (
    (codecs.BOM_UTF8, "utf-8-sig"),
    # UTF-32 before UTF-16, as the UTF-32-LE BOM starts with the UTF-16-LE BOM.
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)
_ARGUMENT_RE = re.compile(r'"([^"]*)"|(\S+)')
_INDEX_TIME_RE = re.compile(r"^(\d+):(\d{1,2}):(\d{1,2})$")
_DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
_YEAR_RE = re.compile(r"^(\d{4})\b")


class CueError(Exception):
    """The CUE sheet cannot be used."""


@dataclasses.dataclass
class CueTrack:
    """One audio track in a CUE sheet."""

    number: int
    """The track number as written in the sheet."""

    file: str
    """The audio file name as written in the sheet."""

    start: int
    """Where the track starts in the file, in milliseconds (`INDEX 01`)."""

    end: int | None = None
    """Where the track ends in the file, in milliseconds.

    `None` if the track plays to the end of the file.
    """

    title: str | None = None
    performer: str | None = None
    songwriter: str | None = None
    genre: str | None = None
    date: str | None = None
    disc_no: int | None = None


@dataclasses.dataclass
class CueSheet:
    """A parsed CUE sheet."""

    title: str | None = None
    performer: str | None = None
    genre: str | None = None
    date: str | None = None
    disc_no: int | None = None
    tracks: list[CueTrack] = dataclasses.field(default_factory=list)

    @property
    def files(self) -> list[str]:
        """The distinct audio file names, in order of first use."""
        return list(dict.fromkeys(track.file for track in self.tracks))


def decode(data: bytes, encodings: Sequence[str] = DEFAULT_ENCODINGS) -> str:
    """Decode the bytes of a CUE sheet.

    A byte order mark is trusted. Otherwise each encoding is tried in order, and
    the first that decodes all the bytes wins. UTF-8 is always tried first, as
    it is unlikely that text in another encoding is also valid UTF-8. If no
    encoding works, the text is decoded as UTF-8 with replacement characters,
    so that the sheet is still usable.
    """
    for bom, encoding in _BOMS:
        if data.startswith(bom):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                break
    candidates = ["utf-8", *encodings]
    for encoding in dict.fromkeys(candidates):
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


def parse_time(value: str) -> int | None:
    """Parse `MM:SS:FF` to milliseconds. There are 75 frames in a second."""
    match = _INDEX_TIME_RE.match(value)
    if match is None:
        return None
    minutes, seconds, frames = (int(part) for part in match.groups())
    return round(
        (minutes * 60 + seconds) * 1000 + frames * 1000 / _FRAMES_PER_SECOND,
    )


def _arguments(text: str) -> list[str]:
    return [quoted or bare for quoted, bare in _ARGUMENT_RE.findall(text)]


def _file_name(text: str) -> str | None:
    """Get the file name from the argument of `FILE`, which is `name type`."""
    text = text.strip()
    if text.startswith('"'):
        end = text.find('"', 1)
        return text[1:end] if end > 0 else text[1:]
    # An unquoted name can contain spaces, so only the last word is the type.
    name, _, _type = text.rpartition(" ")
    return (name or text).strip() or None


def _normalize_date(value: str) -> str | None:
    if _DATE_RE.match(value):
        return value
    if match := _YEAR_RE.match(value):
        return match.group(1)
    return None


def parse(text: str) -> CueSheet:  # noqa: C901, PLR0912, PLR0915
    """Parse the text of a CUE sheet.

    Tracks that are not audio, or that have no `INDEX 01`, are skipped. A track
    ends where the next track in the same file starts.

    Raises:
        CueError: If there are no usable tracks.
    """
    sheet = CueSheet()
    current_file: str | None = None
    track: CueTrack | None = None
    skip_track = False

    for raw_line in text.lstrip("﻿").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        command, _, rest = line.partition(" ")
        command = command.upper()
        rest = rest.strip()

        if command == "FILE":
            current_file = _file_name(rest)
            track = None
            skip_track = False
        elif command == "TRACK":
            args = rest.split()
            track = None
            skip_track = True
            if current_file is None or len(args) < 2 or not args[0].isdigit():  # noqa: PLR2004
                continue
            if args[1].upper() != "AUDIO":
                continue
            skip_track = False
            # The start is unknown until INDEX 01, which a usable track has.
            track = CueTrack(number=int(args[0]), file=current_file, start=-1)
            sheet.tracks.append(track)
        elif command == "INDEX":
            args = rest.split()
            if skip_track or track is None or len(args) < 2:  # noqa: PLR2004
                continue
            if args[0].isdigit() and int(args[0]) == 1:
                time = parse_time(args[1])
                if time is not None:
                    track.start = time
        elif command in ("TITLE", "PERFORMER", "SONGWRITER"):
            args = _arguments(rest)
            value = args[0] if args else None
            attribute = command.lower()
            if track is not None:
                setattr(track, attribute, value)
            elif not skip_track and not sheet.tracks:
                if attribute != "songwriter":
                    setattr(sheet, attribute, value)
        elif command == "REM":
            key, _, value = rest.partition(" ")
            args = _arguments(value)
            value = args[0] if args else ""
            key = key.upper()
            if key == "GENRE" and value:
                if track is not None:
                    track.genre = value
                elif not sheet.tracks:
                    sheet.genre = value
            elif key == "DATE":
                date = _normalize_date(value)
                if track is not None:
                    track.date = date
                elif not sheet.tracks:
                    sheet.date = date
            elif key == "DISCNUMBER" and value.isdigit() and track is None:
                sheet.disc_no = int(value)

    sheet.tracks = [t for t in sheet.tracks if t.start >= 0]
    if not sheet.tracks:
        msg = "The CUE sheet has no audio tracks"
        raise CueError(msg)

    _set_track_ends(sheet.tracks)
    for t in sheet.tracks:
        # Per-track values fall back to the album values.
        t.performer = t.performer or sheet.performer
        t.genre = t.genre or sheet.genre
        t.date = t.date or sheet.date
        t.disc_no = t.disc_no or sheet.disc_no
    return sheet


def _set_track_ends(tracks: list[CueTrack]) -> None:
    for track, following in zip(tracks, tracks[1:], strict=False):
        if following.file == track.file and following.start > track.start:
            track.end = following.start


def parse_bytes(data: bytes, encodings: Sequence[str] = DEFAULT_ENCODINGS) -> CueSheet:
    """Decode and parse a CUE sheet."""
    return parse(decode(data, encodings))


def find_audio_file(cue_path: pathlib.Path, name: str) -> pathlib.Path | None:
    """Find the audio file that a CUE sheet names.

    The name is relative to the directory of the CUE sheet. Names written on
    Windows are accepted, but only their last part is used if the path is
    absolute. If there is no file with the exact name, the match is tried in
    these ways, and the first that finds a file wins:

    1. The same name, ignoring case.
    2. The same name without extension, with an audio file extension.
    """
    directory = cue_path.parent
    normalized = name.replace("\\", "/")
    if re.match(r"^[A-Za-z]:", normalized) or normalized.startswith("/"):
        normalized = normalized.rsplit("/", 1)[-1]
    relative = pathlib.PurePosixPath(normalized)
    if ".." in relative.parts:
        return None

    candidate = directory.joinpath(*relative.parts)
    if candidate.is_file():
        return candidate

    try:
        siblings = {
            entry.name.lower(): entry
            for entry in candidate.parent.iterdir()
            if entry.is_file() and entry != cue_path
        }
    except OSError:
        return None
    if (match := siblings.get(candidate.name.lower())) is not None:
        return match
    stem = candidate.stem.lower()
    for extension in AUDIO_EXTENSIONS:
        if (match := siblings.get(stem + extension)) is not None:
            return match
    return None
