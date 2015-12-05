from __future__ import absolute_import, unicode_literals

import random

import mock

from mopidy.models import Playlist, Ref, Track
from mopidy.mpd.protocol import stored_playlists

from tests.mpd import protocol


class IssueGH17RegressionTest(protocol.BaseTestCase):

    """
    The issue: http://github.com/mopidy/mopidy/issues/17

    How to reproduce:

    - Play a playlist where one track cannot be played
    - Turn on random mode
    - Press next until you get to the unplayable track
    """

    def test(self):
        tracks = [
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
            Track(uri='dummy:error'),
            Track(uri='dummy:d'),
            Track(uri='dummy:e'),
            Track(uri='dummy:f'),
        ]
        self.audio.trigger_fake_playback_failure('dummy:error')
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=[t.uri for t in tracks]).get()

        random.seed(1)  # Playlist order: abcfde

        self.send_request('play')
        self.assertEqual(
            'dummy:a', self.core.playback.current_track.get().uri)
        self.send_request('random "1"')
        self.send_request('next')
        self.assertEqual(
            'dummy:b', self.core.playback.current_track.get().uri)
        self.send_request('next')
        # Should now be at track 'c', but playback fails and it skips ahead
        self.assertEqual(
            'dummy:f', self.core.playback.current_track.get().uri)
        self.send_request('next')
        self.assertEqual(
            'dummy:d', self.core.playback.current_track.get().uri)
        self.send_request('next')
        self.assertEqual(
            'dummy:e', self.core.playback.current_track.get().uri)


class IssueGH18RegressionTest(protocol.BaseTestCase):

    """
    The issue: http://github.com/mopidy/mopidy/issues/18

    How to reproduce:

        Play, random on, next, random off, next, next.

        At this point it gives the same song over and over.
    """

    def test(self):
        tracks = [
            Track(uri='dummy:a'), Track(uri='dummy:b'), Track(uri='dummy:c'),
            Track(uri='dummy:d'), Track(uri='dummy:e'), Track(uri='dummy:f'),
        ]
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=[t.uri for t in tracks]).get()

        random.seed(1)

        self.send_request('play')
        self.send_request('random "1"')
        self.send_request('next')
        self.send_request('random "0"')
        self.send_request('next')

        self.send_request('next')
        tl_track_1 = self.core.playback.current_tl_track.get()
        self.send_request('next')
        tl_track_2 = self.core.playback.current_tl_track.get()
        self.send_request('next')
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
        tracks = [
            Track(uri='dummy:a'), Track(uri='dummy:b'), Track(uri='dummy:c'),
            Track(uri='dummy:d'), Track(uri='dummy:e'), Track(uri='dummy:f'),
        ]
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=[t.uri for t in tracks]).get()

        random.seed(1)

        self.send_request('play')
        self.send_request('random "1"')
        self.send_request('deleteid "1"')
        self.send_request('deleteid "2"')
        self.send_request('deleteid "3"')
        self.send_request('deleteid "4"')
        self.send_request('deleteid "5"')
        self.send_request('deleteid "6"')
        self.send_request('status')


class IssueGH69RegressionTest(protocol.BaseTestCase):

    """
    The issue: https://github.com/mopidy/mopidy/issues/69

    How to reproduce:

        Play track, stop, clear current playlist, load a new playlist, status.

        The status response now contains "song: None".
    """

    def test(self):
        self.core.playlists.create('foo')

        tracks = [
            Track(uri='dummy:a'), Track(uri='dummy:b'), Track(uri='dummy:c'),
            Track(uri='dummy:d'), Track(uri='dummy:e'), Track(uri='dummy:f'),
        ]
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=[t.uri for t in tracks]).get()

        self.send_request('play')
        self.send_request('stop')
        self.send_request('clear')
        self.send_request('load "foo"')
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

        self.send_request('lsinfo "/"')
        self.assertInResponse(
            u'playlist: all lart spotify:track:\w\{22\} pastes')

        self.send_request(
            r'listplaylistinfo "all lart spotify:track:\\w\\{22\\} pastes"')
        self.assertInResponse('OK')


class IssueGH137RegressionTest(protocol.BaseTestCase):

    """
    The issue: https://github.com/mopidy/mopidy/issues/137

    How to reproduce:

    - Send "list" query with mismatching quotes
    """

    def test(self):
        self.send_request(
            u'list Date Artist "Anita Ward" '
            u'Album "This Is Remixed Hits - Mashups & Rare 12" Mixes"')

        self.assertInResponse('ACK [2@0] {list} Invalid unquoted character')


class IssueGH1120RegressionTest(protocol.BaseTestCase):
    """
    The issue: https://github.com/mopidy/mopidy/issues/1120

    How to reproduce:

    - A playlist must be in both browse results and playlists
    - Call for instance ``lsinfo "/"`` to populate the cache with the
      playlist name from the playlist backend.
    - Call ``lsinfo "/dummy"`` to override the playlist name with the browse
      name.
    - Call ``lsinfo "/"`` and we now have an invalid name with ``/`` in it.

    """

    @mock.patch.object(stored_playlists, '_get_last_modified')
    def test(self, last_modified_mock):
        last_modified_mock.return_value = '2015-08-05T22:51:06Z'
        self.backend.library.dummy_browse_result = {
            'dummy:/': [Ref.playlist(name='Top 100 tracks', uri='dummy:/1')],
        }
        self.backend.playlists.set_dummy_playlists([
            Playlist(name='Top 100 tracks', uri='dummy:/1'),
        ])

        response1 = self.send_request('lsinfo "/"')
        self.send_request('lsinfo "/dummy"')

        response2 = self.send_request('lsinfo "/"')
        self.assertEqual(response1, response2)


class IssueGH1348RegressionTest(protocol.BaseTestCase):

    """
    The issue: http://github.com/mopidy/mopidy/issues/1348
    """

    def test(self):
        self.backend.library.dummy_library = [Track(uri='dummy:a')]

        # Create a dummy playlist and trigger population of mapping
        self.send_request('playlistadd "testing1" "dummy:a"')
        self.send_request('listplaylists')

        # Create an other playlist which isn't in the map
        self.send_request('playlistadd "testing2" "dummy:a"')
        self.assertEqual(['OK'], self.send_request('rm "testing2"'))

        playlists = self.backend.playlists.as_list().get()
        self.assertEqual(['testing1'], [ref.name for ref in playlists])
