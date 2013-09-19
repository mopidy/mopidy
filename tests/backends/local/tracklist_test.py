from __future__ import unicode_literals

import unittest

from mopidy.backends.local import actor
from mopidy.models import Track

from tests import path_to_data_dir
from tests.backends.base.tracklist import TracklistControllerTest
from tests.backends.local import generate_song


class LocalTracklistControllerTest(TracklistControllerTest, unittest.TestCase):
    backend_class = actor.LocalBackend
    config = {
        'local': {
            'media_dir': path_to_data_dir(''),
            'playlists_dir': b'',
            'tag_cache_file': path_to_data_dir('empty_tag_cache'),
        }
    }
    tracks = [
        Track(uri=generate_song(i), length=4464) for i in range(1, 4)]
