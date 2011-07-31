import sys

from mopidy import settings
from mopidy.backends.local import LocalBackend
from mopidy.models import Track

from tests import unittest
from tests.backends.base.current_playlist import CurrentPlaylistControllerTest
from tests.backends.local import generate_song


@unittest.skipIf(sys.platform == 'win32',
    'Our Windows build server does not support GStreamer yet')
class LocalCurrentPlaylistControllerTest(CurrentPlaylistControllerTest,
        unittest.TestCase):

    backend_class = LocalBackend
    tracks = [Track(uri=generate_song(i), length=4464)
        for i in range(1, 4)]

    def setUp(self):
        settings.BACKENDS = ('mopidy.backends.local.LocalBackend',)
        super(LocalCurrentPlaylistControllerTest, self).setUp()

    def tearDown(self):
        super(LocalCurrentPlaylistControllerTest, self).tearDown()
        settings.runtime.clear()
