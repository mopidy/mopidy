from mopidy.mixers import BaseMixer

class GStreamerSoftwareMixer(BaseMixer):
    """Mixer which uses GStreamer to control volume in software."""

    def __init__(self, *args, **kwargs):
        super(GStreamerSoftwareMixer, self).__init__(*args, **kwargs)

    def _get_volume(self):
        return self.backend.output.get_volume()

    def _set_volume(self, volume):
        self.backend.output.set_volume(volume)
