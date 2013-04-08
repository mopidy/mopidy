from __future__ import unicode_literals

from mopidy.backends.local import actor

from tests import unittest, path_to_data_dir
from tests.backends.base import events


class LocalBackendEventsTest(events.BackendEventsTest, unittest.TestCase):
    backend_class = actor.LocalBackend
    config = {
        'local': {
            'music_path': path_to_data_dir(''),
            'playlist_path': '',
            'tag_cache_file': path_to_data_dir('empty_tag_cache'),
        }
    }
