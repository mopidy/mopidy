import glob
import glib
import logging
import os
import shutil

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy import audio, core, settings
from mopidy.backends import base
from mopidy.models import Playlist, Track, Album

from .translator import parse_m3u, parse_mpd_tag_cache

logger = logging.getLogger(u'mopidy.backends.local')


class LocalBackend(ThreadingActor, base.Backend):
    """
    A backend for playing music from a local music archive.

    **Dependencies:**

    - None

    **Settings:**

    - :attr:`mopidy.settings.LOCAL_MUSIC_PATH`
    - :attr:`mopidy.settings.LOCAL_PLAYLIST_PATH`
    - :attr:`mopidy.settings.LOCAL_TAG_CACHE_FILE`
    """

    def __init__(self, *args, **kwargs):
        super(LocalBackend, self).__init__(*args, **kwargs)

        self.current_playlist = core.CurrentPlaylistController(backend=self)

        library_provider = LocalLibraryProvider(backend=self)
        self.library = core.LibraryController(backend=self,
            provider=library_provider)

        playback_provider = base.BasePlaybackProvider(backend=self)
        self.playback = LocalPlaybackController(backend=self,
            provider=playback_provider)

        stored_playlists_provider = LocalStoredPlaylistsProvider(backend=self)
        self.stored_playlists = core.StoredPlaylistsController(backend=self,
            provider=stored_playlists_provider)

        self.uri_schemes = [u'file']

        self.audio = None

    def on_start(self):
        audio_refs = ActorRegistry.get_by_class(audio.Audio)
        assert len(audio_refs) == 1, \
            'Expected exactly one running Audio instance.'
        self.audio = audio_refs[0].proxy()


class LocalPlaybackController(core.PlaybackController):
    def __init__(self, *args, **kwargs):
        super(LocalPlaybackController, self).__init__(*args, **kwargs)

        # XXX Why do we call stop()? Is it to set GStreamer state to 'READY'?
        self.stop()

    @property
    def time_position(self):
        return self.backend.audio.get_position().get()


class LocalStoredPlaylistsProvider(base.BaseStoredPlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(LocalStoredPlaylistsProvider, self).__init__(*args, **kwargs)
        self._folder = settings.LOCAL_PLAYLIST_PATH
        self.refresh()

    def lookup(self, uri):
        pass # TODO

    def refresh(self):
        playlists = []

        logger.info('Loading playlists from %s', self._folder)

        for m3u in glob.glob(os.path.join(self._folder, '*.m3u')):
            name = os.path.basename(m3u)[:-len('.m3u')]
            tracks = []
            for uri in parse_m3u(m3u, settings.LOCAL_MUSIC_PATH):
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


class LocalLibraryProvider(base.BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(LocalLibraryProvider, self).__init__(*args, **kwargs)
        self._uri_mapping = {}
        self.refresh()

    def refresh(self, uri=None):
        tracks = parse_mpd_tag_cache(settings.LOCAL_TAG_CACHE_FILE,
            settings.LOCAL_MUSIC_PATH)

        logger.info('Loading tracks in %s from %s', settings.LOCAL_MUSIC_PATH,
            settings.LOCAL_TAG_CACHE_FILE)

        for track in tracks:
            self._uri_mapping[track.uri] = track

    def lookup(self, uri):
        try:
            return self._uri_mapping[uri]
        except KeyError:
            logger.debug(u'Failed to lookup "%s"', uri)
            return None

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
