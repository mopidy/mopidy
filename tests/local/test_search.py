from __future__ import unicode_literals

import unittest

from mopidy.local import search
from mopidy.models import Album, Track


class LocalLibrarySearchTest(unittest.TestCase):

    def test_find_exact_with_album_query(self):
        expected_tracks = [Track(album=Album(name='foo'))]
        tracks = [Track(), Track(album=Album(name='bar'))] + expected_tracks

        search_result = search.find_exact(tracks, {'album': ['foo']})

        self.assertEqual(search_result.tracks, tuple(expected_tracks))
