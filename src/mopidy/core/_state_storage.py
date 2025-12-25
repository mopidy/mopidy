from __future__ import annotations

import gzip
import logging
import pathlib
import tempfile
from typing import Literal

from pydantic.fields import Field
from pydantic.types import NonNegativeInt  # noqa: TC002

from mopidy.models import Ref, TlTrack  # noqa: TC001
from mopidy.models._base import BaseModel
from mopidy.types import DurationMs, Percentage, PlaybackState, TracklistId

logger = logging.getLogger(__name__)


class HistoryTrack(BaseModel):
    """A track that has been played back at a given timestamp.

    Internally used for save/load state.
    """

    model: Literal["HistoryTrack"] = Field(
        default="HistoryTrack",
        repr=False,
        alias="__model__",
    )

    # The timestamp when the track was played. Read-only.
    timestamp: NonNegativeInt

    # The track reference. Read-only.
    track: Ref


class HistoryState(BaseModel):
    """State of the history controller.

    Internally used for save/load state.
    """

    model: Literal["HistoryState"] = Field(
        default="HistoryState",
        repr=False,
        alias="__model__",
    )

    # The track history. Read-only.
    history: tuple[HistoryTrack, ...] = ()


class MixerControllerState(BaseModel):
    """State of the mixer controller.

    Internally used for save/load state.
    """

    model: Literal["MixerState"] = Field(
        default="MixerState",
        repr=False,
        alias="__model__",
    )

    # The volume. Read-only.
    volume: Percentage | None = None

    # The mute state. Read-only.
    mute: bool | None = None


class PlaybackControllerState(BaseModel):
    """State of the playback controller.

    Internally used for save/load state.
    """

    model: Literal["PlaybackState"] = Field(
        default="PlaybackState",
        repr=False,
        alias="__model__",
    )

    # The tlid of current playing track. Read-only.
    tlid: TracklistId | None = Field(default=None, ge=1)

    # The playback position in milliseconds. Read-only.
    time_position: DurationMs = DurationMs(0)

    # The playback state. Read-only.
    state: PlaybackState = PlaybackState.STOPPED


class TracklistControllerState(BaseModel):
    """State of the tracklist controller.

    Internally used for save/load state.
    """

    model: Literal["TracklistState"] = Field(
        default="TracklistState",
        repr=False,
        alias="__model__",
    )

    # The repeat mode. Read-only.
    repeat: bool = False

    # The consume mode. Read-only.
    consume: bool = False

    # The random mode. Read-only.
    random: bool = False

    # The single mode. Read-only.
    single: bool = False

    # The id of the track to play. Read-only.
    next_tlid: TracklistId = TracklistId(1)

    # The list of tracks. Read-only.
    tl_tracks: tuple[TlTrack, ...] = ()


class CoreControllersState(BaseModel):
    """State of all Core controllers.

    Internally used for save/load state.
    """

    model: Literal["CoreState"] = Field(
        default="CoreState",
        repr=False,
        alias="__model__",
    )

    # State of the history controller.
    history: HistoryState = Field(default_factory=HistoryState)

    # State of the mixer controller.
    mixer: MixerControllerState = Field(default_factory=MixerControllerState)

    # State of the playback controller.
    playback: PlaybackControllerState = Field(default_factory=PlaybackControllerState)

    # State of the tracklist controller.
    tracklist: TracklistControllerState = Field(
        default_factory=TracklistControllerState
    )


class StoredState(BaseModel):
    """State of the core that is persisted to disk.

    Internally used for save/load state.
    """

    model: Literal["StoredState"] = Field(
        default="StoredState",
        repr=False,
        alias="__model__",
    )

    # The version of the state file. Read-only.
    version: str

    # The state of the core. Read-only.
    state: CoreControllersState

    @staticmethod
    def load(path: pathlib.Path) -> StoredState | None:
        """Load state from file."""
        # TODO: raise an exception in case of error?
        if not path.is_file():
            logger.info("File does not exist: %s", path)
            return None
        try:
            with gzip.open(str(path), "rb") as fp:
                return StoredState.model_validate_json(fp.read())
        except (OSError, ValueError) as exc:
            logger.warning(f"Loading JSON failed: {exc}")
            return None

    def dump(self, path: pathlib.Path) -> None:
        """Dump state to file."""
        # TODO: cleanup directory/basename.* files.
        tmp = tempfile.NamedTemporaryFile(  # noqa: SIM115
            prefix=path.name + ".",
            dir=str(path.parent),
            delete=False,
        )
        tmp_path = pathlib.Path(tmp.name)

        try:
            data_string = self.model_dump_json(indent=2, by_alias=True)
            with gzip.GzipFile(fileobj=tmp, mode="wb") as fp:
                fp.write(data_string.encode())
            tmp_path.rename(path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
