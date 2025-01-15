import logging
import os
from typing import TYPE_CHECKING

from mopidy.audio.listener import AudioListener
from mopidy.audio.utils import BaseAudioProxy, _make_audio_proxy
from mopidy.types import PlaybackState

logger = logging.getLogger(__name__)

backend_name = os.environ.get("MOPIDY_AUDIO_BACKEND", "gst")

if backend_name == "gst":
    from mopidy.audio.gst import scan, tags
    from mopidy.audio.gst.actor import Audio
    from mopidy.audio.gst.utils import supported_uri_schemes
elif backend_name == "ffpmpv":
    from mopidy.audio.ffpmpv import scan, tags
    from mopidy.audio.ffpmpv.actor import MpvAudio as Audio
    from mopidy.audio.ffpmpv.utils import supported_uri_schemes
elif backend_name == "dummy":
    from mopidy.audio.dummy import scan, tags
    from mopidy.audio.dummy.actor import DummyAudio as Audio
    from mopidy.audio.dummy.utils import supported_uri_schemes
else:
    msg = f"Unknown audio backend name: {backend_name}"
    raise ValueError(msg)

if TYPE_CHECKING:
    AudioProxy = BaseAudioProxy
else:
    AudioProxy = _make_audio_proxy(Audio)


__all__ = [
    "Audio",
    "AudioListener",
    "AudioProxy",
    "PlaybackState",  # Re-exported for backwards compatibility.
    "scan",
    "supported_uri_schemes",
    "tags",
]
