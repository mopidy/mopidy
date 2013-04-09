from __future__ import unicode_literals

import glob
import logging
import os
import shutil

from mopidy.backends import base, listener
from mopidy.models import Playlist
from mopidy.utils import formatting, path

from .translator import parse_m3u


logger = logging.getLogger('mopidy.backends.local')


class LocalPlaylistsProvider(base.BasePlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(LocalPlaylistsProvider, self).__init__(*args, **kwargs)
        self._media_dir = self.backend.config['local']['media_dir']
        self._playlists_dir = self.backend.config['local']['playlists_dir']
        self.refresh()

    def create(self, name):
        name = formatting.slugify(name)
        uri = path.path_to_uri(self._get_m3u_path(name))
        playlist = Playlist(uri=uri, name=name)
        return self.save(playlist)

    def delete(self, uri):
        playlist = self.lookup(uri)
        if not playlist:
            return

        self._playlists.remove(playlist)
        self._delete_m3u(playlist.uri)

    def lookup(self, uri):
        for playlist in self._playlists:
            if playlist.uri == uri:
                return playlist

    def refresh(self):
        playlists = []

        for m3u in glob.glob(os.path.join(self._playlists_dir, '*.m3u')):
            uri = path.path_to_uri(m3u)
            name = os.path.splitext(os.path.basename(m3u))[0]

            tracks = []
            for track_uri in parse_m3u(m3u, self._media_dir):
                try:
                    # TODO We must use core.library.lookup() to support tracks
                    # from other backends
                    tracks += self.backend.library.lookup(track_uri)
                except LookupError as ex:
                    logger.warning('Playlist item could not be added: %s', ex)

            playlist = Playlist(uri=uri, name=name, tracks=tracks)
            playlists.append(playlist)

        self.playlists = playlists
        listener.BackendListener.send('playlists_loaded')

        logger.info(
            'Loaded %d local playlists from %s',
            len(playlists), self._playlists_dir)

    def save(self, playlist):
        assert playlist.uri, 'Cannot save playlist without URI'

        old_playlist = self.lookup(playlist.uri)

        if old_playlist and playlist.name != old_playlist.name:
            playlist = playlist.copy(name=formatting.slugify(playlist.name))
            playlist = self._rename_m3u(playlist)

        self._save_m3u(playlist)

        if old_playlist is not None:
            index = self._playlists.index(old_playlist)
            self._playlists[index] = playlist
        else:
            self._playlists.append(playlist)

        return playlist

    def _get_m3u_path(self, name):
        name = formatting.slugify(name)
        file_path = os.path.join(self._playlists_dir, name + '.m3u')
        path.check_file_path_is_inside_base_dir(file_path, self._playlists_dir)
        return file_path

    def _save_m3u(self, playlist):
        file_path = path.uri_to_path(playlist.uri)
        path.check_file_path_is_inside_base_dir(file_path, self._playlists_dir)
        with open(file_path, 'w') as file_handle:
            for track in playlist.tracks:
                if track.uri.startswith('file://'):
                    uri = path.uri_to_path(track.uri)
                else:
                    uri = track.uri
                file_handle.write(uri + '\n')

    def _delete_m3u(self, uri):
        file_path = path.uri_to_path(uri)
        path.check_file_path_is_inside_base_dir(file_path, self._playlists_dir)
        if os.path.exists(file_path):
            os.remove(file_path)

    def _rename_m3u(self, playlist):
        src_file_path = path.uri_to_path(playlist.uri)
        path.check_file_path_is_inside_base_dir(
            src_file_path, self._playlists_dir)

        dst_file_path = self._get_m3u_path(playlist.name)
        path.check_file_path_is_inside_base_dir(
            dst_file_path, self._playlists_dir)

        shutil.move(src_file_path, dst_file_path)

        return playlist.copy(uri=path.path_to_uri(dst_file_path))
