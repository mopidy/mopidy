from pykka.actor import ThreadingActor
from pykka.proxy import ActorProxy
from pykka.registry import ActorRegistry

from mopidy.mixers.base import BaseMixer

class GStreamerSoftwareMixer(ThreadingActor, BaseMixer):
    """Mixer which uses GStreamer to control volume in software."""

    def __init__(self):
        # XXX Get reference to output without hardcoding GStreamerOutput
        output_refs = ActorRegistry.get_by_class_name('GStreamerOutput')
        self.output = ActorProxy(output_refs[0])

    def _get_volume(self):
        return self.output.get_volume().get()

    def _set_volume(self, volume):
        self.output.set_volume(volume).get()
