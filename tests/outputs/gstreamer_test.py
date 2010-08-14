import multiprocessing
import unittest

from mopidy.utils import path_to_uri
from mopidy.process import pickle_connection
from mopidy.outputs.gstreamer import GStreamerOutput

from tests import data_folder

class GStreamerOutputTest(unittest.TestCase):
    def setUp(self):
        self.song_uri = path_to_uri(data_folder('song1.wav')) 
        self.output_queue = multiprocessing.Queue()
        self.core_queue = multiprocessing.Queue()
        self.output = GStreamerOutput(self.core_queue, self.output_queue)

    def tearDown(self):
        self.output.destroy()

    def send(self, message):
        (my_end, other_end) = multiprocessing.Pipe()
        message.update({'reply_to': pickle_connection(other_end)})
        self.output_queue.put(message)
        my_end.poll(None)
        return my_end.recv()

    def test_play_uri_existing_file(self):
        message = {'command': 'play_uri', 'uri': self.song_uri}
        self.assertEqual(True, self.send(message))

    def test_play_uri_non_existing_file(self):
        message = {'command': 'play_uri', 'uri': self.song_uri + 'bogus'}
        self.assertEqual(False, self.send(message))
           
