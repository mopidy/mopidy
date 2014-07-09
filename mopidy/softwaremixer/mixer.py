from __future__ import unicode_literals

import logging

import pykka

from mopidy import mixer


logger = logging.getLogger(__name__)


class SoftwareMixer(pykka.ThreadingActor, mixer.Mixer):

    name = 'software'

    def __init__(self, config, audio):
        super(SoftwareMixer, self).__init__()
        self.audio = audio

        logger.info('Mixing using GStreamer software mixing')

    def get_volume(self):
        return self.audio.get_volume().get()

    def set_volume(self, volume):
        self.audio.set_volume(volume)
        self.trigger_volume_changed(volume)

    def get_mute(self):
        return self.audio.get_mute().get()

    def set_mute(self, muted):
        self.audio.set_mute(muted)
        self.trigger_mute_changed(muted)
