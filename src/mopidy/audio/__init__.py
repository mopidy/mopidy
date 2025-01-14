from mopidy.audio.gst import scan, tags
from mopidy.audio.gst.actor import Audio
from mopidy.audio.gst.utils import supported_uri_schemes
from mopidy.audio.listener import AudioListener
from mopidy.audio.utils import _make_audio_proxy
from mopidy.types import PlaybackState

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
