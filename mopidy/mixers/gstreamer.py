from mopidy.mixers import BaseMixer

class GStreamerMixer(BaseMixer):
    """Mixer which uses GStreamer to control volume."""

    def __init__(self, *args, **kwargs):
        super(GStreamerMixer, self).__init__(*args, **kwargs)

    def _get_volume(self):
        # TODO Get volume from GStreamerProcess

    def _set_volume(self, volume):
        # TODO Send volume to GStreamerProcess

