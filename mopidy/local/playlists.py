from __future__ import absolute_import, division, unicode_literals

import glob
import logging
import operator
import os
import sys

from mopidy import backend
from mopidy.models import Playlist, Ref

from .translator import local_playlist_uri_to_path, path_to_local_playlist_uri
from .translator import parse_m3u

logger = logging.getLogger(__name__)


def _ref(playlist):
    return Ref.playlist(uri=playlist.uri, name=playlist.name)


class LocalPlaylistsProvider(backend.PlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(LocalPlaylistsProvider, self).__init__(*args, **kwargs)
        self._media_dir = self.backend.config['local']['media_dir']
        self._playlists_dir = self.backend.config['local']['playlists_dir']
        self._playlists = {}
        self.refresh()

    def get_playlists(self, ref=True):
        if ref:
            playlists = map(_ref, self._playlists.values())
        else:
            playlists = self._playlists.values()
        return sorted(playlists, key=operator.attrgetter('name'))

    @property
    def playlists(self):
        return self.get_playlists(ref=False)

    @playlists.setter
    def playlists(self, playlists):
        self._playlists = {playlist.uri: playlist for playlist in playlists}

    def create(self, name):
        playlist = self._save_m3u(Playlist(name=name))
        self._playlists[playlist.uri] = playlist
        return playlist

    def delete(self, uri):
        if uri in self._playlists:
            path = local_playlist_uri_to_path(uri, self._playlists_dir)
            if os.path.exists(path):
                os.remove(path)
            else:
                logger.warn('Trying to delete missing playlist file %s', path)
            del self._playlists[uri]
        else:
            logger.warn('Trying to delete unknown playlist %s', uri)

    def lookup(self, uri):
        return self._playlists[uri]

    def refresh(self):
        playlists = {}
        encoding = sys.getfilesystemencoding()
        for path in glob.glob(os.path.join(self._playlists_dir, b'*.m3u')):
            relpath = os.path.basename(path)
            uri = path_to_local_playlist_uri(relpath)
            name = os.path.splitext(relpath)[0].decode(encoding)
            tracks = parse_m3u(path, self._media_dir)
            playlists[uri] = Playlist(uri=uri, name=name, tracks=tracks)
        self._playlists = playlists

        logger.info(
            'Loaded %d local playlists from %s',
            len(playlists), self._playlists_dir)

    def save(self, playlist):
        assert playlist.uri, 'Cannot save playlist without URI'

        uri = playlist.uri
        # TODO: require existing (created) playlist - currently, this
        # is a *should* in https://docs.mopidy.com/en/latest/api/core/
        playlist = self._save_m3u(playlist)
        if uri != playlist.uri and uri in self._playlists:
            path = local_playlist_uri_to_path(uri, self._playlists_dir)
            if os.path.exists(path):
                os.remove(path)
            else:
                logger.warn('Trying to delete missing playlist file %s', path)
        self._playlists[uri] = playlist
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
