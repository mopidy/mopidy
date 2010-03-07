import alsaaudio

from mopidy.mixers import BaseMixer

class AlsaMixer(BaseMixer):
    def __init__(self):
        self._mixer = alsaaudio.Mixer()

    def _get_volume(self):
        return self._mixer.getvolume()[0]

    def _set_volume(self, volume):
        self._mixer.setvolume(volume)
