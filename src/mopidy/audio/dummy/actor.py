from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from mopidy.audio import AudioListener
from mopidy.audio.base.audio import AudioBase
from mopidy.types import PlaybackState

if TYPE_CHECKING:
    from mopidy.config import Config
    from mopidy.mixer import MixerProxy
    from mopidy.types import DurationMs

logger = logging.getLogger(__name__)


class DummyAudio(AudioBase):
    def __init__(self, config: Config, mixer: MixerProxy | None) -> None:
        super().__init__(config, mixer)
        self._last_playback_start_time = None
        self._last_playback_paused_time = None
        self._state = PlaybackState.STOPPED
        self._uri = None

    def set_uri(self, uri: str, live_stream: bool, download: bool) -> None:  # noqa: ARG002
        logger.info("Would now play URI %s", uri)
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
        logger.info("Would now start playback")
        self._last_playback_start_time = time.time()
        self._last_playback_paused_time = None
        self.state = PlaybackState.PLAYING
        return True

    def pause_playback(self) -> bool:
        logger.info("Would now pause playback")
        self._last_playback_paused_time = time.time()
        self.state = PlaybackState.PAUSED
        return True

    def stop_playback(self) -> bool:
        logger.info("Would now stop playback")
        self._last_playback_start_time = None
        self._last_playback_paused_time = None
        self._uri = None
        self.state = PlaybackState.STOPPED
        return True

    def _get_position(self) -> int:
        if self._last_playback_paused_time is not None:
            return int(
                self._last_playback_paused_time - (self._last_playback_start_time or 0)
            )
        if self._last_playback_start_time:
            return int(time.time() - self._last_playback_start_time)
        return 0

    def get_position(self) -> int:
        pos = self._get_position()
        logger.debug("returning position %d", pos)
        return pos

    def set_position(self, position: DurationMs) -> bool:
        logger.info("Would now seek to %d", position)
        return True
