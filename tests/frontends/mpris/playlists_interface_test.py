from __future__ import unicode_literals

import datetime
import mock
import unittest

import pykka

try:
    import dbus
except ImportError:
    dbus = False

from mopidy import core
from mopidy.audio import PlaybackState
from mopidy.backends import dummy
from mopidy.models import Track

if dbus:
    from mopidy.frontends.mpris import objects


@unittest.skipUnless(dbus, 'dbus not found')
class PlayerInterfaceTest(unittest.TestCase):
    def setUp(self):
        objects.MprisObject._connect_to_dbus = mock.Mock()
        self.backend = dummy.create_dummy_backend_proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()
        self.mpris = objects.MprisObject(config={}, core=self.core)

        foo = self.core.playlists.create('foo').get()
        foo = foo.copy(last_modified=datetime.datetime(2012, 3, 1, 6, 0, 0))
        foo = self.core.playlists.save(foo).get()

        bar = self.core.playlists.create('bar').get()
        bar = bar.copy(last_modified=datetime.datetime(2012, 2, 1, 6, 0, 0))
        bar = self.core.playlists.save(bar).get()

        baz = self.core.playlists.create('baz').get()
        baz = baz.copy(last_modified=datetime.datetime(2012, 1, 1, 6, 0, 0))
        baz = self.core.playlists.save(baz).get()
        self.playlist = baz

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_activate_playlist_appends_tracks_to_tracklist(self):
        self.core.tracklist.add([
            Track(uri='dummy:old-a'),
            Track(uri='dummy:old-b'),
        ])
        self.playlist = self.playlist.copy(tracks=[
            Track(uri='dummy:baz-a'),
            Track(uri='dummy:baz-b'),
            Track(uri='dummy:baz-c'),
        ])
        self.playlist = self.core.playlists.save(self.playlist).get()

        self.assertEqual(2, self.core.tracklist.length.get())

        playlists = self.mpris.GetPlaylists(0, 100, 'User', False)
        playlist_id = playlists[2][0]
        self.mpris.ActivatePlaylist(playlist_id)

        self.assertEqual(5, self.core.tracklist.length.get())
        self.assertEqual(
            PlaybackState.PLAYING, self.core.playback.state.get())
        self.assertEqual(
            self.playlist.tracks[0], self.core.playback.current_track.get())

    def test_activate_empty_playlist_is_harmless(self):
        self.assertEqual(0, self.core.tracklist.length.get())

        playlists = self.mpris.GetPlaylists(0, 100, 'User', False)
        playlist_id = playlists[2][0]
        self.mpris.ActivatePlaylist(playlist_id)

        self.assertEqual(0, self.core.tracklist.length.get())
        self.assertEqual(
            PlaybackState.STOPPED, self.core.playback.state.get())
        self.assertIsNone(self.core.playback.current_track.get())

    def test_get_playlists_in_alphabetical_order(self):
        result = self.mpris.GetPlaylists(0, 100, 'Alphabetical', False)

        self.assertEqual(3, len(result))

        self.assertEqual('/com/mopidy/playlist/MR2W23LZHJRGC4Q_', result[0][0])
        self.assertEqual('bar', result[0][1])

        self.assertEqual('/com/mopidy/playlist/MR2W23LZHJRGC6Q_', result[1][0])
        self.assertEqual('baz', result[1][1])

        self.assertEqual('/com/mopidy/playlist/MR2W23LZHJTG63Y_', result[2][0])
        self.assertEqual('foo', result[2][1])

    def test_get_playlists_in_reverse_alphabetical_order(self):
        result = self.mpris.GetPlaylists(0, 100, 'Alphabetical', True)

        self.assertEqual(3, len(result))
        self.assertEqual('foo', result[0][1])
        self.assertEqual('baz', result[1][1])
        self.assertEqual('bar', result[2][1])

    def test_get_playlists_in_modified_order(self):
        result = self.mpris.GetPlaylists(0, 100, 'Modified', False)

        self.assertEqual(3, len(result))
        self.assertEqual('baz', result[0][1])
        self.assertEqual('bar', result[1][1])
        self.assertEqual('foo', result[2][1])

    def test_get_playlists_in_reverse_modified_order(self):
        result = self.mpris.GetPlaylists(0, 100, 'Modified', True)

        self.assertEqual(3, len(result))
        self.assertEqual('foo', result[0][1])
        self.assertEqual('bar', result[1][1])
        self.assertEqual('baz', result[2][1])

    def test_get_playlists_in_user_order(self):
        result = self.mpris.GetPlaylists(0, 100, 'User', False)

        self.assertEqual(3, len(result))
        self.assertEqual('foo', result[0][1])
        self.assertEqual('bar', result[1][1])
        self.assertEqual('baz', result[2][1])

    def test_get_playlists_in_reverse_user_order(self):
        result = self.mpris.GetPlaylists(0, 100, 'User', True)

        self.assertEqual(3, len(result))
        self.assertEqual('baz', result[0][1])
        self.assertEqual('bar', result[1][1])
        self.assertEqual('foo', result[2][1])

    def test_get_playlists_slice_on_start_of_list(self):
        result = self.mpris.GetPlaylists(0, 2, 'User', False)

        self.assertEqual(2, len(result))
        self.assertEqual('foo', result[0][1])
        self.assertEqual('bar', result[1][1])

    def test_get_playlists_slice_later_in_list(self):
        result = self.mpris.GetPlaylists(2, 2, 'User', False)

        self.assertEqual(1, len(result))
        self.assertEqual('baz', result[0][1])

    def test_get_playlist_count_returns_number_of_playlists(self):
        result = self.mpris.Get(objects.PLAYLISTS_IFACE, 'PlaylistCount')

        self.assertEqual(3, result)

    def test_get_orderings_includes_alpha_modified_and_user(self):
        result = self.mpris.Get(objects.PLAYLISTS_IFACE, 'Orderings')

        self.assertIn('Alphabetical', result)
        self.assertNotIn('Created', result)
        self.assertIn('Modified', result)
        self.assertNotIn('Played', result)
        self.assertIn('User', result)

    def test_get_active_playlist_does_not_return_a_playlist(self):
        result = self.mpris.Get(objects.PLAYLISTS_IFACE, 'ActivePlaylist')
        valid, playlist = result
        playlist_id, playlist_name, playlist_icon_uri = playlist

        self.assertEqual(False, valid)
        self.assertEqual('/', playlist_id)
        self.assertEqual('None', playlist_name)
        self.assertEqual('', playlist_icon_uri)
