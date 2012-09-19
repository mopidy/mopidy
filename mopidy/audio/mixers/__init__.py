import pygst
pygst.require('0.10')
import gst
import gobject


def create_track(label, initial_volume, min_volume, max_volume,
                      num_channels, flags):
    class Track(gst.interfaces.MixerTrack):
        def __init__(self):
            super(Track, self).__init__()
            self.volumes = (initial_volume,) * self.num_channels

        @gobject.property
        def label(self):
            return label

        @gobject.property
        def min_volume(self):
            return min_volume

        @gobject.property
        def max_volume(self):
            return max_volume

        @gobject.property
        def num_channels(self):
            return num_channels

        @gobject.property
        def flags(self):
            return flags

    return Track()


# Import all mixers so that they are registered with GStreamer.
#
# Keep these imports at the bottom of the file to avoid cyclic import problems
# when mixers use the above code.
from .auto import AutoAudioMixer
from .fake import FakeMixer
from .nad import NadMixer
