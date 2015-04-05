from __future__ import absolute_import, division, unicode_literals

import glob
import logging
import operator
import os
import re
import sys

from mopidy import backend
from mopidy.m3u import translator
from mopidy.models import Playlist, Ref


logger = logging.getLogger(__name__)


class M3UPlaylistsProvider(backend.PlaylistsProvider):

    # TODO: currently this only handles UNIX file systems
    _invalid_filename_chars = re.compile(r'[/]')

    def __init__(self, *args, **kwargs):
        super(M3UPlaylistsProvider, self).__init__(*args, **kwargs)

        self._playlists_dir = self.backend._config['m3u']['playlists_dir']
        self._playlists = {}
        self.refresh()

    def as_list(self):
        refs = [
            Ref.playlist(uri=pl.uri, name=pl.name)
            for pl in self._playlists.values()]
        return sorted(refs, key=operator.attrgetter('name'))

    def get_items(self, uri):
        playlist = self._playlists.get(uri)
        if playlist is None:
            return None
        return [Ref.track(uri=t.uri, name=t.name) for t in playlist.tracks]

    def create(self, name):
        playlist = self._save_m3u(Playlist(name=name))
        self._playlists[playlist.uri] = playlist
        logger.info('Created playlist %s', playlist.uri)
        return playlist

    def delete(self, uri):
        if uri in self._playlists:
            path = translator.playlist_uri_to_path(uri, self._playlists_dir)
            if os.path.exists(path):
                os.remove(path)
            else:
                logger.warn('Trying to delete missing playlist file %s', path)
            del self._playlists[uri]
        else:
            logger.warn('Trying to delete unknown playlist %s', uri)

    def lookup(self, uri):
        return self._playlists.get(uri)

    def refresh(self):
        playlists = {}

        encoding = sys.getfilesystemencoding()
        for path in glob.glob(os.path.join(self._playlists_dir, b'*.m3u')):
            relpath = os.path.basename(path)
            uri = translator.path_to_playlist_uri(relpath)
            name = os.path.splitext(relpath)[0].decode(encoding)
            tracks = translator.parse_m3u(path)
            playlists[uri] = Playlist(uri=uri, name=name, tracks=tracks)

        self._playlists = playlists

        logger.info(
            'Loaded %d M3U playlists from %s',
            len(playlists), self._playlists_dir)

    def save(self, playlist):
        assert playlist.uri, 'Cannot save playlist without URI'
        assert playlist.uri in self._playlists, \
            'Cannot save playlist with unknown URI: %s' % playlist.uri

        original_uri = playlist.uri
        playlist = self._save_m3u(playlist)
        if playlist.uri != original_uri and original_uri in self._playlists:
            self.delete(original_uri)
        self._playlists[playlist.uri] = playlist
        return playlist

    def _write_m3u_extinf(self, file_handle, track):
        title = track.name.encode('latin-1', 'replace')
        runtime = track.length // 1000 if track.length else -1
        file_handle.write('#EXTINF:' + str(runtime) + ',' + title + '\n')

    def _sanitize_m3u_name(self, name, encoding=sys.getfilesystemencoding()):
        name = self._invalid_filename_chars.sub('|', name.strip())
        # make sure we end up with a valid path segment
        name = name.encode(encoding, errors='replace')
        name = os.path.basename(name)  # paranoia?
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
