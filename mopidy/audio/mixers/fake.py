"""Fake mixer for use in tests.

Set the :confval:`audio/mixer:` config value to ``fakemixer`` to use this
mixer.
"""

from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gobject
import gst

from . import utils


class FakeMixer(gst.Element, gst.ImplementsInterface, gst.interfaces.Mixer):
    __gstdetails__ = (
        'FakeMixer',
        'Mixer',
        'Fake mixer for use in tests.',
        'Mopidy')

    track_label = gobject.property(type=str, default='Master')
    track_initial_volume = gobject.property(type=int, default=0)
    track_min_volume = gobject.property(type=int, default=0)
    track_max_volume = gobject.property(type=int, default=100)
    track_num_channels = gobject.property(type=int, default=2)
    track_flags = gobject.property(type=int, default=(
        gst.interfaces.MIXER_TRACK_MASTER | gst.interfaces.MIXER_TRACK_OUTPUT))

    def list_tracks(self):
        track = utils.create_track(
            self.track_label,
            self.track_initial_volume,
            self.track_min_volume,
            self.track_max_volume,
            self.track_num_channels,
            self.track_flags)
        return [track]

    def get_volume(self, track):
        return track.volumes

    def set_volume(self, track, volumes):
        track.volumes = volumes

    def set_record(self, track, record):
        pass
