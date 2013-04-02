from __future__ import unicode_literals

from mopidy import settings
from mopidy.backends.local import actor
from mopidy.models import Track

from tests import unittest, path_to_data_dir
from tests.backends.base.tracklist import TracklistControllerTest
from tests.backends.local import generate_song


class LocalTracklistControllerTest(TracklistControllerTest, unittest.TestCase):
    backend_class = actor.LocalBackend
    tracks = [
        Track(uri=generate_song(i), length=4464) for i in range(1, 4)]
    # TODO: setup config

    def setUp(self):
        settings.LOCAL_TAG_CACHE_FILE = path_to_data_dir('empty_tag_cache')
        super(LocalTracklistControllerTest, self).setUp()

    def tearDown(self):
        super(LocalTracklistControllerTest, self).tearDown()
        settings.runtime.clear()
