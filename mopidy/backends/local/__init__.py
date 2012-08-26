import glob
import glib
import logging
import os
import shutil

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy import settings, DATA_PATH
from mopidy.backends.base import (Backend, CurrentPlaylistController,
    LibraryController, BaseLibraryProvider, PlaybackController,
    BasePlaybackProvider, StoredPlaylistsController,
    BaseStoredPlaylistsProvider)
from mopidy.models import Playlist, Track, Album
from mopidy.gstreamer import GStreamer

from .translator import parse_m3u, parse_mpd_tag_cache

logger = logging.getLogger(u'mopidy.backends.local')

DEFAULT_PLAYLIST_PATH = os.path.join(DATA_PATH, 'playlists')
DEFAULT_TAG_CACHE_FILE = os.path.join(DATA_PATH, 'tag_cache')
DEFAULT_MUSIC_PATH = str(glib.get_user_special_dir(glib.USER_DIRECTORY_MUSIC))

if not DEFAULT_MUSIC_PATH or DEFAULT_MUSIC_PATH == os.path.expanduser(u'~'):
    DEFAULT_MUSIC_PATH = os.path.expanduser(u'~/music')


class LocalBackend(ThreadingActor, Backend):
    """
    A backend for playing music from a local music archive.

    **Issues:** https://github.com/mopidy/mopidy/issues?labels=backend-local

    **Dependencies:**

    - None

    **Settings:**

    - :attr:`mopidy.settings.LOCAL_MUSIC_PATH`
    - :attr:`mopidy.settings.LOCAL_PLAYLIST_PATH`
    - :attr:`mopidy.settings.LOCAL_TAG_CACHE_FILE`
    """

    def __init__(self, *args, **kwargs):
        super(LocalBackend, self).__init__(*args, **kwargs)

        self.current_playlist = CurrentPlaylistController(backend=self)

        library_provider = LocalLibraryProvider(backend=self)
        self.library = LibraryController(backend=self,
            provider=library_provider)

        playback_provider = LocalPlaybackProvider(backend=self)
        self.playback = LocalPlaybackController(backend=self,
            provider=playback_provider)

        stored_playlists_provider = LocalStoredPlaylistsProvider(backend=self)
        self.stored_playlists = StoredPlaylistsController(backend=self,
            provider=stored_playlists_provider)

        self.uri_schemes = [u'file']

        self.gstreamer = None

    def on_start(self):
        gstreamer_refs = ActorRegistry.get_by_class(GStreamer)
        assert len(gstreamer_refs) == 1, \
            'Expected exactly one running GStreamer.'
        self.gstreamer = gstreamer_refs[0].proxy()


class LocalPlaybackController(PlaybackController):
    def __init__(self, *args, **kwargs):
        super(LocalPlaybackController, self).__init__(*args, **kwargs)

        # XXX Why do we call stop()? Is it to set GStreamer state to 'READY'?
        self.stop()

    @property
    def time_position(self):
        return self.backend.gstreamer.get_position().get()


class LocalPlaybackProvider(BasePlaybackProvider):
    def pause(self):
        return self.backend.gstreamer.pause_playback().get()

    def play(self, track):
        self.backend.gstreamer.prepare_change()
        self.backend.gstreamer.set_uri(track.uri).get()
        return self.backend.gstreamer.start_playback().get()

    def resume(self):
        return self.backend.gstreamer.start_playback().get()

    def seek(self, time_position):
        return self.backend.gstreamer.set_position(time_position).get()

    def stop(self):
        return self.backend.gstreamer.stop_playback().get()


class LocalStoredPlaylistsProvider(BaseStoredPlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(LocalStoredPlaylistsProvider, self).__init__(*args, **kwargs)
        self._folder = settings.LOCAL_PLAYLIST_PATH or DEFAULT_PLAYLIST_PATH
        self.refresh()

    def lookup(self, uri):
        pass # TODO

    def refresh(self):
        playlists = []

        logger.info('Loading playlists from %s', self._folder)

        for m3u in glob.glob(os.path.join(self._folder, '*.m3u')):
            name = os.path.basename(m3u)[:len('.m3u')]
            tracks = []
            for uri in parse_m3u(m3u):
                try:
                    tracks.append(self.backend.library.lookup(uri))
                except LookupError, e:
                    logger.error('Playlist item could not be added: %s', e)
            playlist = Playlist(tracks=tracks, name=name)

            # FIXME playlist name needs better handling
            # FIXME tracks should come from lib. lookup

            playlists.append(playlist)

        self.playlists = playlists

    def create(self, name):
        playlist = Playlist(name=name)
        self.save(playlist)
        return playlist

    def delete(self, playlist):
        if playlist not in self._playlists:
            return

        self._playlists.remove(playlist)
        filename = os.path.join(self._folder, playlist.name + '.m3u')

        if os.path.exists(filename):
            os.remove(filename)

    def rename(self, playlist, name):
        if playlist not in self._playlists:
            return

        src = os.path.join(self._folder, playlist.name + '.m3u')
        dst = os.path.join(self._folder, name + '.m3u')

        renamed = playlist.copy(name=name)
        index = self._playlists.index(playlist)
        self._playlists[index] = renamed

        shutil.move(src, dst)

    def save(self, playlist):
        file_path = os.path.join(self._folder, playlist.name + '.m3u')

        # FIXME this should be a save_m3u function, not inside save
        with open(file_path, 'w') as file_handle:
            for track in playlist.tracks:
                if track.uri.startswith('file://'):
                    file_handle.write(track.uri[len('file://'):] + '\n')
                else:
                    file_handle.write(track.uri + '\n')

        self._playlists.append(playlist)


class LocalLibraryProvider(BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(LocalLibraryProvider, self).__init__(*args, **kwargs)
        self._uri_mapping = {}
        self.refresh()

    def refresh(self, uri=None):
        tag_cache = settings.LOCAL_TAG_CACHE_FILE or DEFAULT_TAG_CACHE_FILE
        music_folder = settings.LOCAL_MUSIC_PATH or DEFAULT_MUSIC_PATH

        tracks = parse_mpd_tag_cache(tag_cache, music_folder)

        logger.info('Loading tracks in %s from %s', music_folder, tag_cache)

        for track in tracks:
            self._uri_mapping[track.uri] = track

    def lookup(self, uri):
        try:
            return self._uri_mapping[uri]
        except KeyError:
            raise LookupError('%s not found.' % uri)

    def find_exact(self, **query):
        self._validate_query(query)
        result_tracks = self._uri_mapping.values()

        for (field, values) in query.iteritems():
            if not hasattr(values, '__iter__'):
                values = [values]
            # FIXME this is bound to be slow for large libraries
            for value in values:
                q = value.strip()

                track_filter = lambda t: q == t.name
                album_filter = lambda t: q == getattr(t, 'album', Album()).name
                artist_filter = lambda t: filter(
                    lambda a: q == a.name, t.artists)
                uri_filter = lambda t: q == t.uri
                any_filter = lambda t: (track_filter(t) or album_filter(t) or
                    artist_filter(t) or uri_filter(t))

                if field == 'track':
                    result_tracks = filter(track_filter, result_tracks)
                elif field == 'album':
                    result_tracks = filter(album_filter, result_tracks)
                elif field == 'artist':
                    result_tracks = filter(artist_filter, result_tracks)
                elif field == 'uri':
                    result_tracks = filter(uri_filter, result_tracks)
                elif field == 'any':
                    result_tracks = filter(any_filter, result_tracks)
                else:
                    raise LookupError('Invalid lookup field: %s' % field)
        return Playlist(tracks=result_tracks)

    def search(self, **query):
        self._validate_query(query)
        result_tracks = self._uri_mapping.values()

        for (field, values) in query.iteritems():
            if not hasattr(values, '__iter__'):
                values = [values]
            # FIXME this is bound to be slow for large libraries
            for value in values:
                q = value.strip().lower()

                track_filter  = lambda t: q in t.name.lower()
                album_filter = lambda t: q in getattr(
                    t, 'album', Album()).name.lower()
                artist_filter = lambda t: filter(
                    lambda a: q in a.name.lower(), t.artists)
                uri_filter = lambda t: q in t.uri.lower()
                any_filter = lambda t: track_filter(t) or album_filter(t) or \
                    artist_filter(t) or uri_filter(t)

                if field == 'track':
                    result_tracks = filter(track_filter, result_tracks)
                elif field == 'album':
                    result_tracks = filter(album_filter, result_tracks)
                elif field == 'artist':
                    result_tracks = filter(artist_filter, result_tracks)
                elif field == 'uri':
                    result_tracks = filter(uri_filter, result_tracks)
                elif field == 'any':
                    result_tracks = filter(any_filter, result_tracks)
                else:
                    raise LookupError('Invalid lookup field: %s' % field)
        return Playlist(tracks=result_tracks)

    def _validate_query(self, query):
        for (_, values) in query.iteritems():
            if not values:
                raise LookupError('Missing query')
            for value in values:
                if not value:
                    raise LookupError('Missing query')
