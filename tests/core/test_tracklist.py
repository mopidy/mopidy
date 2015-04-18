from __future__ import absolute_import, unicode_literals

import unittest

import mock

from mopidy import backend, core
from mopidy.models import TlTrack, Track
from mopidy.utils import deprecation


class TracklistTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.tracks = [
            Track(uri='dummy1:a', name='foo'),
            Track(uri='dummy1:b', name='foo'),
            Track(uri='dummy1:c', name='bar'),
        ]

        def lookup(uri):
            future = mock.Mock()
            future.get.return_value = [t for t in self.tracks if t.uri == uri]
            return future

        self.backend = mock.Mock()
        self.backend.uri_schemes.get.return_value = ['dummy1']
        self.library = mock.Mock(spec=backend.LibraryProvider)
        self.library.lookup.side_effect = lookup
        self.backend.library = self.library

        self.core = core.Core(mixer=None, backends=[self.backend])
        self.tl_tracks = self.core.tracklist.add(uris=[
            t.uri for t in self.tracks])

    def test_add_by_uri_looks_up_uri_in_library(self):
        self.library.lookup.reset_mock()
        self.core.tracklist.clear()

        with deprecation.ignore('core.tracklist.add:uri_arg'):
            tl_tracks = self.core.tracklist.add(uris=['dummy1:a'])

        self.library.lookup.assert_called_once_with('dummy1:a')
        self.assertEqual(1, len(tl_tracks))
        self.assertEqual(self.tracks[0], tl_tracks[0].track)
        self.assertEqual(tl_tracks, self.core.tracklist.tl_tracks[-1:])

    def test_add_by_uris_looks_up_uris_in_library(self):
        self.library.lookup.reset_mock()
        self.core.tracklist.clear()

        tl_tracks = self.core.tracklist.add(uris=[t.uri for t in self.tracks])

        self.library.lookup.assert_has_calls([
            mock.call('dummy1:a'),
            mock.call('dummy1:b'),
            mock.call('dummy1:c'),
        ])
        self.assertEqual(3, len(tl_tracks))
        self.assertEqual(self.tracks[0], tl_tracks[0].track)
        self.assertEqual(self.tracks[1], tl_tracks[1].track)
        self.assertEqual(self.tracks[2], tl_tracks[2].track)
        self.assertEqual(
            tl_tracks, self.core.tracklist.tl_tracks[-len(tl_tracks):])

    def test_remove_removes_tl_tracks_matching_query(self):
        tl_tracks = self.core.tracklist.remove({'name': ['foo']})

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

        self.assertEqual(1, self.core.tracklist.length)
        self.assertListEqual(self.tl_tracks[2:], self.core.tracklist.tl_tracks)

    def test_remove_works_with_dict_instead_of_kwargs(self):
        tl_tracks = self.core.tracklist.remove({'name': ['foo']})

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

        self.assertEqual(1, self.core.tracklist.length)
        self.assertListEqual(self.tl_tracks[2:], self.core.tracklist.tl_tracks)

    def test_filter_returns_tl_tracks_matching_query(self):
        tl_tracks = self.core.tracklist.filter({'name': ['foo']})

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

    def test_filter_works_with_dict_instead_of_kwargs(self):
        tl_tracks = self.core.tracklist.filter({'name': ['foo']})

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

    def test_filter_fails_if_values_isnt_iterable(self):
        with self.assertRaises(ValueError):
            self.core.tracklist.filter({'tlid': 3})

    def test_filter_fails_if_values_is_a_string(self):
        with self.assertRaises(ValueError):
            self.core.tracklist.filter({'uri': 'a'})

    # TODO Extract tracklist tests from the local backend tests


class TracklistIndexTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.tracks = [
            Track(uri='dummy1:a', name='foo'),
            Track(uri='dummy1:b', name='foo'),
            Track(uri='dummy1:c', name='bar'),
        ]

        def lookup(uris):
            return {u: [t for t in self.tracks if t.uri == u] for u in uris}

        self.core = core.Core(mixer=None, backends=[])
        self.core.library = mock.Mock(spec=core.LibraryController)
        self.core.library.lookup.side_effect = lookup

        self.core.playback = mock.Mock(spec=core.PlaybackController)

        self.tl_tracks = self.core.tracklist.add(uris=[
            t.uri for t in self.tracks])

    def test_index_returns_index_of_track(self):
        self.assertEqual(0, self.core.tracklist.index(self.tl_tracks[0]))
        self.assertEqual(1, self.core.tracklist.index(self.tl_tracks[1]))
        self.assertEqual(2, self.core.tracklist.index(self.tl_tracks[2]))

    def test_index_returns_none_if_item_not_found(self):
        tl_track = TlTrack(0, Track())
        self.assertEqual(self.core.tracklist.index(tl_track), None)

    def test_index_returns_none_if_called_with_none(self):
        self.assertEqual(self.core.tracklist.index(None), None)

    def test_index_errors_out_for_invalid_tltrack(self):
        with self.assertRaises(ValueError):
            self.core.tracklist.index('abc')

    def test_index_return_index_when_called_with_tlids(self):
        tl_tracks = self.tl_tracks
        self.assertEqual(0, self.core.tracklist.index(tlid=tl_tracks[0].tlid))
        self.assertEqual(1, self.core.tracklist.index(tlid=tl_tracks[1].tlid))
        self.assertEqual(2, self.core.tracklist.index(tlid=tl_tracks[2].tlid))

    def test_index_returns_none_if_tlid_not_found(self):
        self.assertEqual(self.core.tracklist.index(tlid=123), None)

    def test_index_returns_none_if_called_with_tlid_none(self):
        self.assertEqual(self.core.tracklist.index(tlid=None), None)

    def test_index_errors_out_for_invalid_tlid(self):
        with self.assertRaises(ValueError):
            self.core.tracklist.index(tlid=-1)

    def test_index_without_args_returns_current_tl_track_index(self):
        self.core.playback.get_current_tl_track.side_effect = [
            None, self.tl_tracks[0], self.tl_tracks[1], self.tl_tracks[2]]

        self.assertEqual(None, self.core.tracklist.index())
        self.assertEqual(0, self.core.tracklist.index())
        self.assertEqual(1, self.core.tracklist.index())
        self.assertEqual(2, self.core.tracklist.index())
