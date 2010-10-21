import random
import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Track

class IssueGH17RegressionTest(unittest.TestCase):
    """
    The issue: http://github.com/jodal/mopidy/issues#issue/17

    How to reproduce:

    - Play a playlist where one track cannot be played
    - Turn on random mode
    - Press next until you get to the unplayable track
    """

    def setUp(self):
        self.backend = DummyBackend(mixer_class=DummyMixer)
        self.backend.current_playlist.append([
            Track(uri='a'), Track(uri='b'), None,
            Track(uri='d'), Track(uri='e'), Track(uri='f')])
        self.mpd = dispatcher.MpdDispatcher(backend=self.backend)

    def test(self):
        random.seed(1) # Playlist order: abcfde
        self.mpd.handle_request(u'play')
        self.assertEquals('a', self.backend.playback.current_track.uri)
        self.mpd.handle_request(u'random "1"')
        self.mpd.handle_request(u'next')
        self.assertEquals('b', self.backend.playback.current_track.uri)
        self.mpd.handle_request(u'next')
        # Should now be at track 'c', but playback fails and it skips ahead
        self.assertEquals('f', self.backend.playback.current_track.uri)
        self.mpd.handle_request(u'next')
        self.assertEquals('d', self.backend.playback.current_track.uri)
        self.mpd.handle_request(u'next')
        self.assertEquals('e', self.backend.playback.current_track.uri)


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


class IssueGH22RegressionTest(unittest.TestCase):
    """
    The issue: http://github.com/jodal/mopidy/issues/#issue/22

    How to reproduce:

        Play, random on, remove all tracks from the current playlist (as in
        "delete" each one, not "clear").

        Alternatively: Play, random on, remove a random track from the current
        playlist, press next until it crashes.
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
        self.mpd.handle_request(u'deleteid "1"')
        self.mpd.handle_request(u'deleteid "2"')
        self.mpd.handle_request(u'deleteid "3"')
        self.mpd.handle_request(u'deleteid "4"')
        self.mpd.handle_request(u'deleteid "5"')
        self.mpd.handle_request(u'deleteid "6"')
        self.mpd.handle_request(u'status')
