from __future__ import absolute_import, division, unicode_literals

import glob
import logging
import os
import sys

from mopidy import backend
from mopidy.models import Playlist

from .translator import local_playlist_uri_to_path, path_to_local_playlist_uri
from .translator import parse_m3u

logger = logging.getLogger(__name__)


class LocalPlaylistsProvider(backend.PlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(LocalPlaylistsProvider, self).__init__(*args, **kwargs)
        self._media_dir = self.backend.config['local']['media_dir']
        self._playlists_dir = self.backend.config['local']['playlists_dir']
        self.refresh()

    def create(self, name):
        playlist = self._save_m3u(Playlist(name=name))
        old_playlist = self.lookup(playlist.uri)
        if old_playlist is not None:
            index = self._playlists.index(old_playlist)
            self._playlists[index] = playlist
        else:
            self._playlists.append(playlist)
        logger.info('Created playlist %s', playlist.uri)
        return playlist

    def delete(self, uri):
        playlist = self.lookup(uri)
        if not playlist:
            logger.warn('Trying to delete unknown playlist %s', uri)
            return
        path = local_playlist_uri_to_path(uri, self._playlists_dir)
        try:
            os.remove(path)
        except OSError as e:
            logger.error('Error deleting playlist %s: %s', uri, e)
        self._playlists.remove(playlist)
        # TODO: handle in PlaylistsController, playlist_changed?
        backend.BackendListener.send('playlists_loaded')

    def lookup(self, uri):
        # TODO: store as {uri: playlist}?
        for playlist in self._playlists:
            if playlist.uri == uri:
                return playlist

    def refresh(self):
        playlists = []

        for path in glob.glob(os.path.join(self._playlists_dir, '*.m3u')):
            relpath = os.path.basename(path)
            name, _ = os.path.splitext(relpath)
            uri = path_to_local_playlist_uri(relpath)

            tracks = []
            for track in parse_m3u(path, self._media_dir):
                tracks.append(track)

            playlist = Playlist(uri=uri, name=name, tracks=tracks)
            playlists.append(playlist)

        self.playlists = playlists
        # TODO: send what scheme we loaded them for?
        backend.BackendListener.send('playlists_loaded')

        logger.info(
            'Loaded %d local playlists from %s',
            len(playlists), self._playlists_dir)

    def save(self, playlist):
        assert playlist.uri, 'Cannot save playlist without URI'

        uri = playlist.uri
        # TODO: require existing (created) playlist - currently, this
        # is a *should* in https://docs.mopidy.com/en/latest/api/core/
        try:
            index = self._playlists.index(self.lookup(uri))
        except ValueError:
            logger.warn('Saving playlist with new URI %s', uri)
            index = -1

        playlist = self._save_m3u(playlist)
        if index >= 0 and uri != playlist.uri:
            path = local_playlist_uri_to_path(uri, self._playlists_dir)
            try:
                os.remove(path)
            except OSError as e:
                logger.error('Error deleting playlist %s: %s', uri, e)
        if index >= 0:
            self._playlists[index] = playlist
        else:
            self._playlists.append(playlist)
        return playlist

    def _write_m3u_extinf(self, file_handle, track):
        title = track.name.encode('latin-1', 'replace')
        runtime = track.length // 1000 if track.length else -1
        file_handle.write('#EXTINF:' + str(runtime) + ',' + title + '\n')

    def _sanitize_m3u_name(self, name, encoding=sys.getfilesystemencoding()):
        name = name.encode(encoding, errors='replace')
        name = os.path.basename(name)
        name = name.decode(encoding)
        return name

    def _save_m3u(self, playlist, encoding=sys.getfilesystemencoding()):
        if playlist.name:
            name = self._sanitize_m3u_name(playlist.name, encoding)
            uri = path_to_local_playlist_uri(name.encode(encoding) + b'.m3u')
            path = local_playlist_uri_to_path(uri, self._playlists_dir)
        elif playlist.uri:
            uri = playlist.uri
            path = local_playlist_uri_to_path(uri, self._playlists_dir)
            name, _ = os.path.splitext(os.path.basename(path).decode(encoding))
        else:
            raise ValueError('M3U playlist needs name or URI')
        extended = any(track.name for track in playlist.tracks)

        with open(path, 'w') as file_handle:
            if extended:
                file_handle.write('#EXTM3U\n')
            for track in playlist.tracks:
                if extended and track.name:
                    self._write_m3u_extinf(file_handle, track)
                file_handle.write(track.uri + '\n')

        # assert playlist name matches file name/uri
        return playlist.copy(uri=uri, name=name)
