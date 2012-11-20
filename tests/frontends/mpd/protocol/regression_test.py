from __future__ import unicode_literals

import random

from mopidy.models import Track

from tests.frontends.mpd import protocol


class IssueGH17RegressionTest(protocol.BaseTestCase):
    """
    The issue: http://github.com/mopidy/mopidy/issues/17

    How to reproduce:

    - Play a playlist where one track cannot be played
    - Turn on random mode
    - Press next until you get to the unplayable track
    """
    def test(self):
        self.core.tracklist.add([
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
            Track(uri='dummy:error'),
            Track(uri='dummy:d'),
            Track(uri='dummy:e'),
            Track(uri='dummy:f'),
        ])
        random.seed(1)  # Playlist order: abcfde

        self.sendRequest('play')
        self.assertEquals(
            'dummy:a', self.core.playback.current_track.get().uri)
        self.sendRequest('random "1"')
        self.sendRequest('next')
        self.assertEquals(
            'dummy:b', self.core.playback.current_track.get().uri)
        self.sendRequest('next')
        # Should now be at track 'c', but playback fails and it skips ahead
        self.assertEquals(
            'dummy:f', self.core.playback.current_track.get().uri)
        self.sendRequest('next')
        self.assertEquals(
            'dummy:d', self.core.playback.current_track.get().uri)
        self.sendRequest('next')
        self.assertEquals(
            'dummy:e', self.core.playback.current_track.get().uri)


class IssueGH18RegressionTest(protocol.BaseTestCase):
    """
    The issue: http://github.com/mopidy/mopidy/issues/18

    How to reproduce:

        Play, random on, next, random off, next, next.

        At this point it gives the same song over and over.
    """

    def test(self):
        self.core.tracklist.add([
            Track(uri='dummy:a'), Track(uri='dummy:b'), Track(uri='dummy:c'),
            Track(uri='dummy:d'), Track(uri='dummy:e'), Track(uri='dummy:f')])
        random.seed(1)

        self.sendRequest('play')
        self.sendRequest('random "1"')
        self.sendRequest('next')
        self.sendRequest('random "0"')
        self.sendRequest('next')

        self.sendRequest('next')
        tl_track_1 = self.core.playback.current_tl_track.get()
        self.sendRequest('next')
        tl_track_2 = self.core.playback.current_tl_track.get()
        self.sendRequest('next')
        tl_track_3 = self.core.playback.current_tl_track.get()

        self.assertNotEqual(tl_track_1, tl_track_2)
        self.assertNotEqual(tl_track_2, tl_track_3)


class IssueGH22RegressionTest(protocol.BaseTestCase):
    """
    The issue: http://github.com/mopidy/mopidy/issues/22

    How to reproduce:

        Play, random on, remove all tracks from the current playlist (as in
        "delete" each one, not "clear").

        Alternatively: Play, random on, remove a random track from the current
        playlist, press next until it crashes.
    """

    def test(self):
        self.core.tracklist.add([
            Track(uri='dummy:a'), Track(uri='dummy:b'), Track(uri='dummy:c'),
            Track(uri='dummy:d'), Track(uri='dummy:e'), Track(uri='dummy:f')])
        random.seed(1)

        self.sendRequest('play')
        self.sendRequest('random "1"')
        self.sendRequest('deleteid "1"')
        self.sendRequest('deleteid "2"')
        self.sendRequest('deleteid "3"')
        self.sendRequest('deleteid "4"')
        self.sendRequest('deleteid "5"')
        self.sendRequest('deleteid "6"')
        self.sendRequest('status')


class IssueGH69RegressionTest(protocol.BaseTestCase):
    """
    The issue: https://github.com/mopidy/mopidy/issues/69

    How to reproduce:

        Play track, stop, clear current playlist, load a new playlist, status.

        The status response now contains "song: None".
    """

    def test(self):
        self.core.playlists.create('foo')
        self.core.tracklist.add([
            Track(uri='dummy:a'), Track(uri='dummy:b'), Track(uri='dummy:c'),
            Track(uri='dummy:d'), Track(uri='dummy:e'), Track(uri='dummy:f')])

        self.sendRequest('play')
        self.sendRequest('stop')
        self.sendRequest('clear')
        self.sendRequest('load "foo"')
        self.assertNotInResponse('song: None')


class IssueGH113RegressionTest(protocol.BaseTestCase):
    """
    The issue: https://github.com/mopidy/mopidy/issues/113

    How to reproduce:

    - Have a playlist with a name contining backslashes, like
      "all lart spotify:track:\w\{22\} pastes".
    - Try to load the playlist with the backslashes in the playlist name
      escaped.
    """

    def test(self):
        self.core.playlists.create(
            u'all lart spotify:track:\w\{22\} pastes')

        self.sendRequest('lsinfo "/"')
        self.assertInResponse(
            u'playlist: all lart spotify:track:\w\{22\} pastes')

        self.sendRequest(
            r'listplaylistinfo "all lart spotify:track:\\w\\{22\\} pastes"')
        self.assertInResponse('OK')


class IssueGH137RegressionTest(protocol.BaseTestCase):
    """
    The issue: https://github.com/mopidy/mopidy/issues/137

    How to reproduce:

    - Send "list" query with mismatching quotes
    """

    def test(self):
        self.sendRequest(
            u'list Date Artist "Anita Ward" '
            u'Album "This Is Remixed Hits - Mashups & Rare 12" Mixes"')

        self.assertInResponse('ACK [2@0] {list} Invalid unquoted character')
