from __future__ import annotations

import pykka
from pykka.typing import ActorMemberMixin, proxy_field, proxy_method

from mopidy.audio.base.audio import AudioBase


class BaseAudioProxy(ActorMemberMixin, pykka.ActorProxy[AudioBase]):
    pass


def _make_audio_proxy(Audio):  # noqa: N803 (we want this to look like a classname)
    class AudioProxy(ActorMemberMixin, pykka.ActorProxy[Audio]):
        """Audio layer wrapped in a Pykka actor proxy."""

        state = proxy_field(Audio.state)
        set_uri = proxy_method(Audio.set_uri)
        set_source_setup_callback = proxy_method(Audio.set_source_setup_callback)
        set_about_to_finish_callback = proxy_method(Audio.set_about_to_finish_callback)
        get_position = proxy_method(Audio.get_position)
        set_position = proxy_method(Audio.set_position)
        start_playback = proxy_method(Audio.start_playback)
        pause_playback = proxy_method(Audio.pause_playback)
        prepare_change = proxy_method(Audio.prepare_change)
        stop_playback = proxy_method(Audio.stop_playback)
        wait_for_state_change = proxy_method(Audio.wait_for_state_change)
        enable_sync_handler = proxy_method(Audio.enable_sync_handler)
        get_current_tags = proxy_method(Audio.get_current_tags)

    return AudioProxy
