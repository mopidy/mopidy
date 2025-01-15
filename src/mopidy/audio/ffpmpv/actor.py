from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mopidy.audio import AudioListener
from mopidy.audio.base.audio import AudioBase
from mopidy.audio.ffpmpv.mpv import Mpv
from mopidy.types import PlaybackState

if TYPE_CHECKING:
    from mopidy.config import Config
    from mopidy.mixer import MixerProxy
    from mopidy.types import DurationMs

logger = logging.getLogger(__name__)


class MpvAudio(AudioBase):
    def __init__(self, config: Config, mixer: MixerProxy | None) -> None:
        super().__init__(config, mixer)
        self._state = PlaybackState.STOPPED
        self._uri = None
        self._mpv = Mpv()

    def set_uri(self, uri: str, live_stream: bool, download: bool) -> None:  # noqa: ARG002
        self._uri = uri

    @property
    def state(self) -> PlaybackState:
        return self._state

    @state.setter
    def state(self, new_state: PlaybackState) -> None:
        old_state = self._state
        self._state = new_state
        AudioListener.send(
            "state_changed",
            old_state=old_state,
            new_state=new_state,
            target_state=new_state,
        )
        if new_state == PlaybackState.STOPPED:
            AudioListener.send("stream_changed", uri=None)
        else:
            AudioListener.send("stream_changed", uri=self._uri)

    def start_playback(self) -> bool:
        if not self._uri:
            logger.warning("Cannot start playback without URI")
            return False
        self._mpv.play(self._uri)
        self.state = PlaybackState.PLAYING
        return True

    def pause_playback(self) -> bool:
        self._mpv.pause()
        self.state = PlaybackState.PAUSED
        return True

    def stop_playback(self) -> bool:
        self._uri = None
        self._mpv.stop()
        self.state = PlaybackState.STOPPED
        return True

    def get_position(self) -> int:
        if self.state != PlaybackState.STOPPED and (
            pos := self._mpv.get_position_seconds()
        ):
            return int(pos * 1000)
        return 0

    def set_position(self, position: DurationMs) -> bool:
        if self.state != PlaybackState.STOPPED:
            self._mpv.set_position_seconds(position / 1000.0)
            return True
        return False
