from __future__ import unicode_literals

import gobject

import pygst
pygst.require('0.10')
import gst  # noqa

from mopidy.audio.mixers.auto import AutoAudioMixer
from mopidy.audio.mixers.fake import FakeMixer


def register_mixer(mixer_class):
    gobject.type_register(mixer_class)
    gst.element_register(
        mixer_class, mixer_class.__name__.lower(), gst.RANK_MARGINAL)


def register_mixers():
    register_mixer(AutoAudioMixer)
    register_mixer(FakeMixer)
