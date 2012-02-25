from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy.mixers.base import BaseMixer
from mopidy.gstreamer import GStreamer

class GStreamerSoftwareMixer(ThreadingActor, BaseMixer):
    """Mixer which uses GStreamer to control volume in software."""

    def __init__(self):
        super(GStreamerSoftwareMixer, self).__init__()
        self.output = None

    def on_start(self):
        output_refs = ActorRegistry.get_by_class(GStreamer)
        assert len(output_refs) == 1, 'Expected exactly one running output.'
        self.output = output_refs[0].proxy()

    def get_volume(self):
        return self.output.get_volume().get()

    def set_volume(self, volume):
        self.output.set_volume(volume).get()
