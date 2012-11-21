from __future__ import unicode_literals

from mopidy import settings
from mopidy.backends.local import LocalBackend
from mopidy.models import Track

from tests import unittest
from tests.backends.base.tracklist import TracklistControllerTest
from tests.backends.local import generate_song


class LocalTracklistControllerTest(TracklistControllerTest, unittest.TestCase):
    backend_class = LocalBackend
    tracks = [
        Track(uri=generate_song(i), length=4464) for i in range(1, 4)]

    def setUp(self):
        settings.BACKENDS = ('mopidy.backends.local.LocalBackend',)
        super(LocalTracklistControllerTest, self).setUp()

    def tearDown(self):
        super(LocalTracklistControllerTest, self).tearDown()
        settings.runtime.clear()
