from __future__ import unicode_literals

import glob
import logging
import os
import shutil

from mopidy.backends import base, listener
from mopidy.models import Playlist, Track
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
        uri = 'local:playlist:%s.m3u' % name
        playlist = Playlist(uri=uri, name=name)
        return self.save(playlist)

    def delete(self, uri):
        playlist = self.lookup(uri)
        if not playlist:
            return

        self._playlists.remove(playlist)
        self._delete_m3u(playlist.uri)

    def lookup(self, uri):
        # TODO: store as {uri: playlist}?
        for playlist in self._playlists:
            if playlist.uri == uri:
                return playlist

    def refresh(self):
        playlists = []

        for m3u in glob.glob(os.path.join(self._playlists_dir, '*.m3u')):
            name = os.path.splitext(os.path.basename(m3u))[0]
            uri = 'local:playlist:%s' % name

            tracks = []
            for track_uri in parse_m3u(m3u, self._media_dir):
                result = self.backend.library.lookup(track_uri)
                if result:
                    tracks += self.backend.library.lookup(track_uri)
                else:
                    tracks.append(Track(uri=track_uri))

            playlist = Playlist(uri=uri, name=name, tracks=tracks)
            playlists.append(playlist)

        self.playlists = playlists
        # TODO: send what scheme we loaded them for?
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

    def _m3u_uri_to_path(self, uri):
        # TODO: create uri handling helpers for local uri types.
        file_path = path.uri_to_path(uri).split(':', 1)[1]
        file_path = os.path.join(self._playlists_dir, file_path)
        path.check_file_path_is_inside_base_dir(file_path, self._playlists_dir)
        return file_path

    def _save_m3u(self, playlist):
        file_path = self._m3u_uri_to_path(playlist.uri)
        with open(file_path, 'w') as file_handle:
            for track in playlist.tracks:
                file_handle.write(track.uri + '\n')

    def _delete_m3u(self, uri):
        file_path = self._m3u_uri_to_path(uri)
        if os.path.exists(file_path):
            os.remove(file_path)

    def _rename_m3u(self, playlist):
        dst_name = formatting.slugify(playlist.name)
        dst_uri = 'local:playlist:%s.m3u' % dst_name

        src_file_path = self._m3u_uri_to_path(playlist.uri)
        dst_file_path = self._m3u_uri_to_path(dst_uri)

        shutil.move(src_file_path, dst_file_path)
        return playlist.copy(uri=dst_uri)
