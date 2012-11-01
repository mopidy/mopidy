import glob
import logging
import os
import re
import shutil
import unicodedata

from mopidy import settings
from mopidy.backends import base
from mopidy.models import Playlist
from mopidy.utils import path

from .translator import parse_m3u


logger = logging.getLogger(u'mopidy.backends.local')


class LocalStoredPlaylistsProvider(base.BaseStoredPlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(LocalStoredPlaylistsProvider, self).__init__(*args, **kwargs)
        self._path = settings.LOCAL_PLAYLIST_PATH
        self.refresh()

    def create(self, name):
        name = self._slugify(name)
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
        logger.info('Loading playlists from %s', self._path)

        playlists = []

        for m3u in glob.glob(os.path.join(self._path, '*.m3u')):
            uri = path.path_to_uri(m3u)
            name = os.path.splitext(os.path.basename(m3u))[0]

            tracks = []
            for track_uri in parse_m3u(m3u, settings.LOCAL_MUSIC_PATH):
                try:
                    # TODO We must use core.library.lookup() to support tracks
                    # from other backends
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
            playlist = playlist.copy(name=self._slugify(playlist.name))
            playlist = self._rename_m3u(playlist)

        self._save_m3u(playlist)

        if old_playlist is not None:
            index = self._playlists.index(old_playlist)
            self._playlists[index] = playlist
        else:
            self._playlists.append(playlist)

        return playlist

    def _get_m3u_path(self, name):
        name = self._slugify(name)
        file_path = os.path.join(self._path, name + '.m3u')
        self._validate_file_path(file_path)
        return file_path

    def _save_m3u(self, playlist):
        file_path = path.uri_to_path(playlist.uri)
        self._validate_file_path(file_path)
        with open(file_path, 'w') as file_handle:
            for track in playlist.tracks:
                if track.uri.startswith('file://'):
                    uri = path.uri_to_path(track.uri)
                else:
                    uri = track.uri
                file_handle.write(uri + '\n')

    def _delete_m3u(self, uri):
        file_path = path.uri_to_path(uri)
        self._validate_file_path(file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    def _rename_m3u(self, playlist):
        src_file_path = path.uri_to_path(playlist.uri)
        self._validate_file_path(src_file_path)

        dst_file_path = self._get_m3u_path(playlist.name)
        self._validate_file_path(dst_file_path)

        shutil.move(src_file_path, dst_file_path)

        return playlist.copy(uri=path.path_to_uri(dst_file_path))

    def _validate_file_path(self, file_path):
        assert not file_path.endswith(os.sep), (
            'File path %s cannot end with a path separator' % file_path)

        # Expand symlinks
        real_base_path = os.path.realpath(self._path)
        real_file_path = os.path.realpath(file_path)

        # Use dir of file for prefix comparision, so we don't accept
        # /tmp/foo.m3u as being inside /tmp/foo, simply because they have a
        # common prefix, /tmp/foo, which matches the base path, /tmp/foo.
        real_dir_path = os.path.dirname(real_file_path)

        # Check if dir of file is the base path or a subdir
        common_prefix = os.path.commonprefix([real_base_path, real_dir_path])
        assert common_prefix == real_base_path, (
            'File path %s must be in %s' % (real_file_path, real_base_path))

    def _slugify(self, value):
        """
        Converts to lowercase, removes non-word characters (alphanumerics and
        underscores) and converts spaces to hyphens. Also strips leading and
        trailing whitespace.

        This function is based on Django's slugify implementation.
        """
        value = unicodedata.normalize('NFKD', value)
        value = value.encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        return re.sub(r'[-\s]+', '-', value)
