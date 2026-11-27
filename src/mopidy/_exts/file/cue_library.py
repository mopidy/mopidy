"""CUE sheets as albums in the file extension.

A CUE sheet is shown as an album. Its tracks have URIs like
`file:///music/Album.cue#3`, where the number after `#` is the position of the
track in the sheet, starting at 1. That is not the track number that the sheet
says, as sheets can number their tracks any way they like.
"""

from __future__ import annotations

import dataclasses
import logging
import pathlib
import threading
import urllib.parse
from collections.abc import Callable, Sequence

from mopidy._lib import paths
from mopidy.media import MediaReader, MediaReaderError
from mopidy.models import Album, Artist, Track
from mopidy.types import DurationMs, Uri

from . import cue

logger = logging.getLogger(__name__)

CUE_SUFFIX = ".cue"


def is_cue_path(path: pathlib.Path) -> bool:
    return path.suffix.lower() == CUE_SUFFIX


def split_cue_uri(uri: Uri | str) -> tuple[Uri, int | None] | None:
    """Split a URI of a CUE sheet or one of its tracks.

    Returns the URI of the CUE sheet, and the position of the track in the
    sheet starting at 1. The position is `None` for the URI of the whole sheet,
    and 0, which is no track, if the fragment is not a position. Returns `None`
    if the URI is not for a CUE sheet.
    """
    parts = urllib.parse.urlsplit(uri)
    if parts.scheme != "file" or not is_cue_path(paths.uri_to_path(uri)):
        return None
    sheet_uri = Uri(urllib.parse.urlunsplit(parts._replace(fragment="")))
    if not parts.fragment:
        return sheet_uri, None
    if not parts.fragment.isdecimal():
        return sheet_uri, 0
    return sheet_uri, int(parts.fragment)


def make_track_uri(sheet_uri: Uri, position: int) -> Uri:
    return Uri(f"{sheet_uri}#{position}")


@dataclasses.dataclass(frozen=True)
class CueTarget:
    """A track of a CUE sheet that is found in an audio file."""

    position: int
    """The position of the track in the sheet, starting at 1."""

    track: cue.CueTrack
    audio_path: pathlib.Path
    start: DurationMs
    end: DurationMs | None


@dataclasses.dataclass(frozen=True)
class CueAlbum:
    """A CUE sheet with the audio files found for it."""

    path: pathlib.Path
    uri: Uri
    sheet: cue.CueSheet
    targets: tuple[CueTarget, ...]
    last_modified: int

    @property
    def audio_paths(self) -> set[pathlib.Path]:
        return {target.audio_path.resolve() for target in self.targets}


class CueLibrary:
    """Reads CUE sheets, and keeps what it read until the sheets change."""

    def __init__(
        self,
        *,
        media_reader: MediaReader,
        encodings: Sequence[str],
        is_allowed: Callable[[pathlib.Path], bool],
    ) -> None:
        self._media_reader = media_reader
        self._encodings = tuple(encodings) or cue.DEFAULT_ENCODINGS
        self._is_allowed = is_allowed
        self._lock = threading.Lock()
        self._albums: dict[pathlib.Path, tuple[tuple[int, int], CueAlbum | None]] = {}
        self._lengths: dict[pathlib.Path, tuple[tuple[int, int], DurationMs | None]] = {}

    def load(self, path: pathlib.Path) -> CueAlbum | None:
        """Read a CUE sheet.

        Returns `None` if the sheet cannot be used. The reason is logged.
        """
        try:
            stat = path.stat()
        except OSError:
            return None
        key = (stat.st_mtime_ns, stat.st_size)
        with self._lock:
            cached = self._albums.get(path)
        if cached is not None and cached[0] == key:
            return cached[1]

        album = self._read(path, last_modified=stat.st_mtime_ns // 1_000_000)
        with self._lock:
            self._albums[path] = (key, album)
        return album

    def _read(self, path: pathlib.Path, *, last_modified: int) -> CueAlbum | None:
        uri = paths.path_to_uri(path)
        try:
            sheet = cue.parse_bytes(path.read_bytes(), self._encodings)
        except (OSError, cue.CueError) as exc:
            logger.warning("Cannot use CUE sheet %s: %s", uri, exc)
            return None

        found: dict[str, pathlib.Path | None] = {}
        for name in sheet.files:
            audio_path = cue.find_audio_file(path, name)
            if audio_path is not None and not self._is_allowed(audio_path):
                logger.debug("CUE sheet %s names a file that is not allowed", uri)
                audio_path = None
            if audio_path is None:
                logger.warning("CUE sheet %s names the missing file %r", uri, name)
            found[name] = audio_path

        targets = tuple(
            CueTarget(
                position=position,
                track=track,
                audio_path=audio_path,
                start=DurationMs(track.start),
                end=None if track.end is None else DurationMs(track.end),
            )
            for position, track in enumerate(sheet.tracks, start=1)
            if (audio_path := found[track.file]) is not None
        )
        if not targets:
            return None
        return CueAlbum(
            path=path,
            uri=uri,
            sheet=sheet,
            targets=targets,
            last_modified=last_modified,
        )

    def find_target(self, uri: Uri | str) -> CueTarget | None:
        """Find the part of an audio file that a CUE track URI is for."""
        split = split_cue_uri(uri)
        if split is None or split[1] is None:
            return None
        sheet_uri, position = split
        album = self.load(paths.uri_to_path(sheet_uri))
        if album is None:
            return None
        return next((t for t in album.targets if t.position == position), None)

    def make_tracks(self, album: CueAlbum, position: int | None = None) -> list[Track]:
        """Make the tracks of a CUE sheet, or only the one at the position."""
        sheet = album.sheet
        model_album = Album(
            uri=album.uri,
            name=sheet.title,
            artists=_artists(sheet.performer),
            num_tracks=len(sheet.tracks),
            date=sheet.date,
        )
        tracks = []
        for target in album.targets:
            if position is not None and target.position != position:
                continue
            cue_track = target.track
            tracks.append(
                Track(
                    uri=make_track_uri(album.uri, target.position),
                    name=cue_track.title or f"Track {cue_track.number:02d}",
                    artists=_artists(cue_track.performer),
                    album=model_album,
                    composers=_artists(cue_track.songwriter),
                    genre=cue_track.genre,
                    track_no=cue_track.number,
                    disc_no=cue_track.disc_no,
                    date=cue_track.date,
                    length=self._length(target),
                    last_modified=album.last_modified,
                )
            )
        return tracks

    def _length(self, target: CueTarget) -> DurationMs | None:
        if target.end is not None:
            return DurationMs(target.end - target.start)
        # The last track in a file plays to the end of the file.
        file_length = self._file_length(target.audio_path)
        if file_length is None or file_length <= target.start:
            return None
        return DurationMs(file_length - target.start)

    def _file_length(self, path: pathlib.Path) -> DurationMs | None:
        try:
            stat = path.stat()
        except OSError:
            return None
        key = (stat.st_mtime_ns, stat.st_size)
        with self._lock:
            cached = self._lengths.get(path)
        if cached is not None and cached[0] == key:
            return cached[1]

        try:
            info = self._media_reader.read_media_info(paths.path_to_uri(path))
            length = info.track.length
        except MediaReaderError as exc:
            logger.debug("Cannot read the length of %s: %s", path, exc)
            return None  # Not cached, as it could be a timeout.
        with self._lock:
            self._lengths[path] = (key, length)
        return length


def _artists(name: str | None) -> frozenset[Artist]:
    return frozenset([Artist(name=name)]) if name else frozenset()
