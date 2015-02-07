from __future__ import unicode_literals

import pykka

from mopidy import mixer


def create_proxy(config=None):
    return DummyMixer.start(config=None).proxy()


class DummyMixer(pykka.ThreadingActor, mixer.Mixer):

    def __init__(self, config):
        super(DummyMixer, self).__init__()
        self._volume = None
        self._mute = None

    def get_volume(self):
        return self._volume

    def set_volume(self, volume):
        self._volume = volume
        self.trigger_volume_changed(volume=volume)
        return True

    def get_mute(self):
        return self._mute

    def set_mute(self, mute):
        self._mute = mute
        self.trigger_mute_changed(mute=mute)
        return True
