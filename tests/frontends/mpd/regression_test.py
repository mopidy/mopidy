import random
import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Track

class IssueGH18RegressionTest(unittest.TestCase):
    """
    The issue: http://github.com/jodal/mopidy/issues#issue/18

    How to reproduce:

        Play, random on, next, random off, next, next.

        At this point it gives the same song over and over.
    """

    def setUp(self):
        self.backend = DummyBackend(mixer_class=DummyMixer)
        self.backend.current_playlist.append([
            Track(uri='a'), Track(uri='b'), Track(uri='c'),
            Track(uri='d'), Track(uri='e'), Track(uri='f')])
        self.mpd = dispatcher.MpdDispatcher(backend=self.backend)

    def test(self):
        random.seed(1)
        self.mpd.handle_request(u'play')
        self.mpd.handle_request(u'random "1"')
        self.mpd.handle_request(u'next')
        self.mpd.handle_request(u'random "0"')
        self.mpd.handle_request(u'next')

        self.mpd.handle_request(u'next')
        cp_track_1 = self.backend.playback.current_cp_track
        self.mpd.handle_request(u'next')
        cp_track_2 = self.backend.playback.current_cp_track
        self.mpd.handle_request(u'next')
        cp_track_3 = self.backend.playback.current_cp_track

        self.assertNotEqual(cp_track_1, cp_track_2)
        self.assertNotEqual(cp_track_2, cp_track_3)
