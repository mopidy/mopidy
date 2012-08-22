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
        self.backend.current_playlist.append([
            Track(uri='a'), Track(uri='b'), None,
            Track(uri='d'), Track(uri='e'), Track(uri='f')])
        random.seed(1) # Playlist order: abcfde

        self.sendRequest(u'play')
        self.assertEquals('a', self.backend.playback.current_track.get().uri)
        self.sendRequest(u'random "1"')
        self.sendRequest(u'next')
        self.assertEquals('b', self.backend.playback.current_track.get().uri)
        self.sendRequest(u'next')
        # Should now be at track 'c', but playback fails and it skips ahead
        self.assertEquals('f', self.backend.playback.current_track.get().uri)
        self.sendRequest(u'next')
        self.assertEquals('d', self.backend.playback.current_track.get().uri)
        self.sendRequest(u'next')
        self.assertEquals('e', self.backend.playback.current_track.get().uri)


class IssueGH18RegressionTest(protocol.BaseTestCase):
    """
    The issue: http://github.com/mopidy/mopidy/issues/18

    How to reproduce:

        Play, random on, next, random off, next, next.

        At this point it gives the same song over and over.
    """

    def test(self):
        self.backend.current_playlist.append([
            Track(uri='a'), Track(uri='b'), Track(uri='c'),
            Track(uri='d'), Track(uri='e'), Track(uri='f')])
        random.seed(1)

        self.sendRequest(u'play')
        self.sendRequest(u'random "1"')
        self.sendRequest(u'next')
        self.sendRequest(u'random "0"')
        self.sendRequest(u'next')

        self.sendRequest(u'next')
        cp_track_1 = self.backend.playback.current_cp_track.get()
        self.sendRequest(u'next')
        cp_track_2 = self.backend.playback.current_cp_track.get()
        self.sendRequest(u'next')
        cp_track_3 = self.backend.playback.current_cp_track.get()

        self.assertNotEqual(cp_track_1, cp_track_2)
        self.assertNotEqual(cp_track_2, cp_track_3)


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
        self.backend.current_playlist.append([
            Track(uri='a'), Track(uri='b'), Track(uri='c'),
            Track(uri='d'), Track(uri='e'), Track(uri='f')])
        random.seed(1)

        self.sendRequest(u'play')
        self.sendRequest(u'random "1"')
        self.sendRequest(u'deleteid "1"')
        self.sendRequest(u'deleteid "2"')
        self.sendRequest(u'deleteid "3"')
        self.sendRequest(u'deleteid "4"')
        self.sendRequest(u'deleteid "5"')
        self.sendRequest(u'deleteid "6"')
        self.sendRequest(u'status')


class IssueGH69RegressionTest(protocol.BaseTestCase):
    """
    The issue: https://github.com/mopidy/mopidy/issues/69

    How to reproduce:

        Play track, stop, clear current playlist, load a new playlist, status.

        The status response now contains "song: None".
    """

    def test(self):
        self.backend.stored_playlists.create('foo')
        self.backend.current_playlist.append([
            Track(uri='a'), Track(uri='b'), Track(uri='c'),
            Track(uri='d'), Track(uri='e'), Track(uri='f')])

        self.sendRequest(u'play')
        self.sendRequest(u'stop')
        self.sendRequest(u'clear')
        self.sendRequest(u'load "foo"')
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
        self.backend.stored_playlists.create(
            u'all lart spotify:track:\w\{22\} pastes')

        self.sendRequest(u'lsinfo "/"')
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
        self.sendRequest(u'list Date Artist "Anita Ward" '
            u'Album "This Is Remixed Hits - Mashups & Rare 12" Mixes"')

        self.assertInResponse('ACK [2@0] {list} Invalid unquoted character')
