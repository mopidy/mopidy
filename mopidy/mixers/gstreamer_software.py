import multiprocessing

from mopidy.mixers import BaseMixer
from mopidy.utils.process import pickle_connection

class GStreamerSoftwareMixer(BaseMixer):
    """Mixer which uses GStreamer to control volume in software."""

    def __init__(self, *args, **kwargs):
        super(GStreamerSoftwareMixer, self).__init__(*args, **kwargs)

    def _get_volume(self):
        my_end, other_end = multiprocessing.Pipe()
        self.backend.output_queue.put({
            'command': 'get_volume',
            'reply_to': pickle_connection(other_end),
        })
        my_end.poll(None)
        return my_end.recv()

    def _set_volume(self, volume):
        self.backend.output_queue.put({
            'command': 'set_volume',
            'volume': volume,
        })
