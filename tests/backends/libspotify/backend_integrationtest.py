# TODO This integration test is work in progress.

import unittest

from mopidy.backends.libspotify import LibspotifyBackend
from mopidy.models import Track

from tests.backends.base.current_playlist import \
    BaseCurrentPlaylistControllerTest
from tests.backends.base.library import BaseLibraryControllerTest
from tests.backends.base.playback import BasePlaybackControllerTest
from tests.backends.base.stored_playlists import \
    BaseStoredPlaylistsControllerTest

uris = [
    'spotify:track:6vqcpVcbI3Zu6sH3ieLDNt',
    'spotify:track:111sulhaZqgsnypz3MkiaW',
    'spotify:track:7t8oznvbeiAPMDRuK0R5ZT',
]

class LibspotifyCurrentPlaylistControllerTest(
        BaseCurrentPlaylistControllerTest, unittest.TestCase):

    backend_class = LibspotifyBackend
    tracks = [Track(uri=uri, length=4464) for i, uri in enumerate(uris)]


class LibspotifyPlaybackControllerTest(
        BasePlaybackControllerTest, unittest.TestCase):

    backend_class = LibspotifyBackend
    tracks = [Track(uri=uri, length=4464) for i, uri in enumerate(uris)]


class LibspotifyStoredPlaylistsControllerTest(
        BaseStoredPlaylistsControllerTest, unittest.TestCase):

    backend_class = LibspotifyBackend


class LibspotifyLibraryControllerTest(
        BaseLibraryControllerTest, unittest.TestCase):

    backend_class = LibspotifyBackend
