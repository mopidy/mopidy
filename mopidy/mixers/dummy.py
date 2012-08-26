from pykka.actor import ThreadingActor

from mopidy.mixers.base import BaseMixer

class DummyMixer(ThreadingActor, BaseMixer):
    """Mixer which just stores and reports the chosen volume."""

    def __init__(self):
        super(DummyMixer, self).__init__()
        self._volume = None

    def get_volume(self):
        return self._volume

    def set_volume(self, volume):
        self._volume = volume
