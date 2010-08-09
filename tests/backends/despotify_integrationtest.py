# TODO This integration test is work in progress.

import unittest

from mopidy.backends.despotify import DespotifyBackend
from mopidy.models import Track

from tests.backends.base import *

uris = [
    'spotify:track:6vqcpVcbI3Zu6sH3ieLDNt',
    'spotify:track:111sulhaZqgsnypz3MkiaW',
    'spotify:track:7t8oznvbeiAPMDRuK0R5ZT',
]

class DespotifyCurrentPlaylistControllerTest(
        BaseCurrentPlaylistControllerTest, unittest.TestCase):
    tracks = [Track(uri=uri, length=4464) for i, uri in enumerate(uris)]
    backend_class = DespotifyBackend


class DespotifyPlaybackControllerTest(
        BasePlaybackControllerTest, unittest.TestCase):
    tracks = [Track(uri=uri, length=4464) for i, uri in enumerate(uris)]
    backend_class = DespotifyBackend


class DespotifyStoredPlaylistsControllerTest(
        BaseStoredPlaylistsControllerTest, unittest.TestCase):
    backend_class = DespotifyBackend


class DespotifyLibraryControllerTest(
        BaseLibraryControllerTest, unittest.TestCase):
    backend_class = DespotifyBackend
