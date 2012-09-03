import pygst
pygst.require('0.10')
import gobject
import gst


def create_fake_track(label, intial_volume, min_volume, max_volume,
                      num_channels, flags):
    class Track(gst.interfaces.MixerTrack):
        def __init__(self):
            super(Track, self).__init__()
            self.volumes = (intial_volume,) * self.num_channels

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


class FakeMixer(gst.Element, gst.ImplementsInterface, gst.interfaces.Mixer):
    __gstdetails__ = ('FakeMixer',
                      'Mixer',
                      'Fake mixer for use in tests.',
                      'Thomas Adamcik')

    track_label = gobject.property(type=str, default='Master')

    track_initial_volume = gobject.property(type=int, default=0)

    track_min_volume = gobject.property(type=int, default=0)

    track_max_volume = gobject.property(type=int, default=100)

    track_num_channels = gobject.property(type=int, default=2)

    track_flags = gobject.property(type=int,
        default=(gst.interfaces.MIXER_TRACK_MASTER |
                 gst.interfaces.MIXER_TRACK_OUTPUT))

    def __init__(self):
        gst.Element.__init__(self)

    def list_tracks(self):
        track = create_fake_track(self.track_label,
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


gobject.type_register(FakeMixer)
gst.element_register (FakeMixer, 'fakemixer', gst.RANK_MARGINAL)
