import unittest
import os
import urllib

from mopidy import settings
from mopidy.backends.gstreamer import GStreamerBackend
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Playlist, Track

from tests.backends.base import *
from tests import SkipTest

folder = os.path.dirname(__file__)
folder = os.path.join(folder, '..', 'data')
folder = os.path.abspath(folder)
song = os.path.join(folder, 'song%s.wav')
generate_song = lambda i: 'file://' + urllib.pathname2url(song % i)

# FIXME can be switched to generic test
class GStreamerCurrentPlaylistHandlerTest(BaseCurrentPlaylistControllerTest, unittest.TestCase):
    tracks = [Track(uri=generate_song(i), id=i, length=4464) for i in range(1, 4)]

    backend_class = GStreamerBackend


class GStreamerPlaybackControllerTest(BasePlaybackControllerTest, unittest.TestCase):
    tracks = [Track(uri=generate_song(i), id=i, length=4464) for i in range(1, 4)]
    backend_class = GStreamerBackend

    def add_track(self, file):
        uri = 'file://' + urllib.pathname2url(os.path.join(folder, file))
        track = Track(uri=uri, id=1, length=4464)
        self.backend.current_playlist.add(track)

    def test_uri_handler(self):
        self.assert_('file://' in self.backend.uri_handlers)

    def test_play_mp3(self):
        self.add_track('blank.mp3')
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    def test_play_ogg(self):
        self.add_track('blank.ogg')
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    def test_play_flac(self):
        self.add_track('blank.flac')
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)


class GStreamerBackendStoredPlaylistsControllerTest(BaseStoredPlaylistsControllerTest,
        unittest.TestCase):

    backend_class = GStreamerBackend

    def test_created_playlist_is_persisted(self):
        self.stored.create('test')
        file = os.path.join(settings.PLAYLIST_FOLDER, 'test.m3u')
        self.assert_(os.path.exists(file))

    def test_saved_playlist_is_persisted(self):
        self.stored.save(Playlist(name='test2'))
        file = os.path.join(settings.PLAYLIST_FOLDER, 'test2.m3u')
        self.assert_(os.path.exists(file))

    def test_deleted_playlist_get_removed(self):
        playlist = self.stored.create('test')
        self.stored.delete(playlist)
        file = os.path.join(settings.PLAYLIST_FOLDER, 'test.m3u')
        self.assert_(not os.path.exists(file))

    def test_renamed_playlist_gets_moved(self):
        playlist = self.stored.create('test')
        self.stored.rename(playlist, 'test2')
        file1 = os.path.join(settings.PLAYLIST_FOLDER, 'test.m3u')
        file2 = os.path.join(settings.PLAYLIST_FOLDER, 'test2.m3u')
        self.assert_(not os.path.exists(file1))
        self.assert_(os.path.exists(file2))

    def test_playlist_contents_get_written_to_disk(self):
        track = Track(uri=generate_song(1))
        uri = track.uri[len('file://'):]
        playlist = Playlist(tracks=[track], name='test')
        file_path = os.path.join(settings.PLAYLIST_FOLDER, 'test.m3u')

        self.stored.save(playlist)

        with open(file_path) as file:
            contents = file.read()

        self.assertEqual(uri, contents.strip())

    def test_playlists_are_loaded_at_startup(self):
        track = Track(uri=generate_song(1))
        uri = track.uri[len('file://'):]
        playlist = Playlist(tracks=[track], name='test')
        file_path = os.path.join(settings.PLAYLIST_FOLDER, 'test.m3u')

        self.stored.save(playlist)

        self.backend.destroy()
        self.backend = self.backend_class(mixer=DummyMixer())
        self.stored = self.backend.stored_playlists

        self.assert_(self.stored.playlists)
        self.assertEqual('test', self.stored.playlists[0].name)
        self.assertEqual(track.uri, self.stored.playlists[0].tracks[0].uri)

    def test_santitising_of_playlist_filenames(self):
        raise SkipTest

    def test_playlist_folder_is_createad(self):
        raise SkipTest

    def test_create_sets_playlist_uri(self):
        raise SkipTest

    def test_save_sets_playlist_uri(self):
        raise SkipTest


class GStreamerBackendLibraryControllerTest(BaseStoredPlaylistsControllerTest,
        unittest.TestCase):

    backend_class = GStreamerBackend


if __name__ == '__main__':
    unittest.main()
