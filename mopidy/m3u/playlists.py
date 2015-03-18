from __future__ import absolute_import, division, unicode_literals

import copy
import glob
import logging
import operator
import os
import sys

from mopidy import backend
from mopidy.m3u import translator
from mopidy.models import Playlist


logger = logging.getLogger(__name__)


class M3UPlaylistsProvider(backend.PlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(M3UPlaylistsProvider, self).__init__(*args, **kwargs)

        self._playlists_dir = self.backend._config['m3u']['playlists_dir']
        self._playlists = []
        self.refresh()

    @property
    def playlists(self):
        return copy.copy(self._playlists)

    @playlists.setter
    def playlists(self, playlists):
        self._playlists = playlists

    def create(self, name):
        playlist = self._save_m3u(Playlist(name=name))
        old_playlist = self.lookup(playlist.uri)
        if old_playlist is not None:
            index = self._playlists.index(old_playlist)
            self._playlists[index] = playlist
        else:
            self._playlists.append(playlist)
        self._playlists.sort(key=operator.attrgetter('name'))
        logger.info('Created playlist %s', playlist.uri)
        return playlist

    def delete(self, uri):
        playlist = self.lookup(uri)
        if not playlist:
            logger.warn('Trying to delete unknown playlist %s', uri)
            return
        path = translator.playlist_uri_to_path(uri, self._playlists_dir)
        if os.path.exists(path):
            os.remove(path)
        else:
            logger.warn('Trying to delete missing playlist file %s', path)
        self._playlists.remove(playlist)

    def lookup(self, uri):
        # TODO: store as {uri: playlist} when get_playlists() gets
        # implemented
        for playlist in self._playlists:
            if playlist.uri == uri:
                return playlist

    def refresh(self):
        playlists = []

        encoding = sys.getfilesystemencoding()
        for path in glob.glob(os.path.join(self._playlists_dir, b'*.m3u')):
            relpath = os.path.basename(path)
            name = os.path.splitext(relpath)[0].decode(encoding)
            uri = translator.path_to_playlist_uri(relpath)

            tracks = []
            for track in translator.parse_m3u(path):
                tracks.append(track)

            playlist = Playlist(uri=uri, name=name, tracks=tracks)
            playlists.append(playlist)

        self.playlists = sorted(playlists, key=operator.attrgetter('name'))

        logger.info(
            'Loaded %d M3U playlists from %s',
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
            path = translator.playlist_uri_to_path(uri, self._playlists_dir)
            if os.path.exists(path):
                os.remove(path)
            else:
                logger.warn('Trying to delete missing playlist file %s', path)
        if index >= 0:
            self._playlists[index] = playlist
        else:
            self._playlists.append(playlist)
        self._playlists.sort(key=operator.attrgetter('name'))
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
            uri = translator.path_to_playlist_uri(
                name.encode(encoding) + b'.m3u')
            path = translator.playlist_uri_to_path(uri, self._playlists_dir)
        elif playlist.uri:
            uri = playlist.uri
            path = translator.playlist_uri_to_path(uri, self._playlists_dir)
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
