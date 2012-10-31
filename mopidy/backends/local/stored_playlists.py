import glob
import logging
import os
import shutil

from mopidy import settings
from mopidy.backends import base
from mopidy.models import Playlist
from mopidy.utils import path

from .translator import parse_m3u


logger = logging.getLogger(u'mopidy.backends.local')


class LocalStoredPlaylistsProvider(base.BaseStoredPlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(LocalStoredPlaylistsProvider, self).__init__(*args, **kwargs)
        self._folder = settings.LOCAL_PLAYLIST_PATH
        self.refresh()

    # TODO playlist names needs safer handling using a slug function

    def create(self, name):
        file_path = os.path.join(self._folder, name + '.m3u')
        uri = path.path_to_uri(file_path)
        playlist = Playlist(uri=uri, name=name)
        self.save(playlist)
        return playlist

    def delete(self, playlist):
        if playlist not in self._playlists:
            return

        self._playlists.remove(playlist)
        filename = os.path.join(self._folder, playlist.name + '.m3u')

        if os.path.exists(filename):
            os.remove(filename)

    def lookup(self, uri):
        for playlist in self._playlists:
            if playlist.uri == uri:
                return playlist

    def refresh(self):
        playlists = []

        logger.info('Loading playlists from %s', self._folder)

        for m3u in glob.glob(os.path.join(self._folder, '*.m3u')):
            uri = path.path_to_uri(m3u)
            name = os.path.splitext(os.path.basename(m3u))[0]
            tracks = []
            for track_uri in parse_m3u(m3u, settings.LOCAL_MUSIC_PATH):
                try:
                    tracks.append(self.backend.library.lookup(track_uri))
                except LookupError as ex:
                    logger.error('Playlist item could not be added: %s', ex)
            playlist = Playlist(uri=uri, name=name, tracks=tracks)

            playlists.append(playlist)

        self.playlists = playlists

    def save(self, playlist):
        assert playlist.uri, 'Cannot save playlist without URI'

        old_playlist = self.lookup(playlist.uri)

        if old_playlist and playlist.name != old_playlist.name:
            src = os.path.join(self._folder, old_playlist.name + '.m3u')
            dst = os.path.join(self._folder, playlist.name + '.m3u')
            shutil.move(src, dst)
            playlist = playlist.copy(uri=path.path_to_uri(dst))

        self._save_m3u(playlist)

        if old_playlist is not None:
            index = self._playlists.index(old_playlist)
            self._playlists[index] = playlist
        else:
            self._playlists.append(playlist)

        return playlist

    def _save_m3u(self, playlist):
        file_path = playlist.uri[len('file://'):]
        with open(file_path, 'w') as file_handle:
            for track in playlist.tracks:
                if track.uri.startswith('file://'):
                    uri = track.uri[len('file://'):]
                else:
                    uri = track.uri
                file_handle.write(uri + '\n')
