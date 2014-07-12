from __future__ import unicode_literals

import logging

import pykka

from mopidy import mixer


logger = logging.getLogger(__name__)


class SoftwareMixer(pykka.ThreadingActor, mixer.Mixer):

    name = 'software'

    def __init__(self, config):
        super(SoftwareMixer, self).__init__(config)

        self.audio = None

        logger.info('Mixing using GStreamer software mixing')

    def get_volume(self):
        if self.audio is None:
            return None
        return self.audio.get_volume().get()

    def set_volume(self, volume):
        if self.audio is None:
            return False
        self.audio.set_volume(volume)
        return True

    def get_mute(self):
        if self.audio is None:
            return None
        return self.audio.get_mute().get()

    def set_mute(self, muted):
        if self.audio is None:
            return False
        self.audio.set_mute(muted)
        return True
