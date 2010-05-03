# TODO This integration test is work in progress.

import unittest

from mopidy.backends.libspotify import LibspotifyBackend
from mopidy.models import Track

from tests.backends.base import *

uris = [
    'spotify:track:6vqcpVcbI3Zu6sH3ieLDNt',
    'spotify:track:111sulhaZqgsnypz3MkiaW',
    'spotify:track:7t8oznvbeiAPMDRuK0R5ZT',
]

class LibspotifyCurrentPlaylistControllerTest(
        BaseCurrentPlaylistControllerTest, unittest.TestCase):
    tracks = [Track(uri=uri, id=i, length=4464) for i, uri in enumerate(uris)]
    backend_class = LibspotifyBackend


class LibspotifyPlaybackControllerTest(
        BasePlaybackControllerTest, unittest.TestCase):
    tracks = [Track(uri=uri, id=i, length=4464) for i, uri in enumerate(uris)]
    backend_class = LibspotifyBackend


class LibspotifyStoredPlaylistsControllerTest(
        BaseStoredPlaylistsControllerTest, unittest.TestCase):
    backend_class = LibspotifyBackend


class LibspotifyLibraryControllerTest(
        BaseLibraryControllerTest, unittest.TestCase):
    backend_class = LibspotifyBackend


# TODO Plug this into the backend under test to avoid music output during
# testing.
class DummyAudioController(object):
    def music_delivery(self, *args, **kwargs):
        pass
