from __future__ import unicode_literals

import logging
import urlparse

import pykka

from mopidy import audio as audio_lib
from mopidy.backends import base
from mopidy.core import listener
from mopidy.models import Track, Album, Artist

logger = logging.getLogger('mopidy.backends.stream')


class StreamBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, config, audio):
        super(StreamBackend, self).__init__()

        self.library = StreamLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.playlists = None
        self.tracklist = StreamTracklistProvider(backend=self)

        self.uri_schemes = audio_lib.supported_uri_schemes(
            config['stream']['protocols'])


# TODO: Should we consider letting lookup know how to expand common playlist
# formats (m3u, pls, etc) for http(s) URIs?
class StreamLibraryProvider(base.BaseLibraryProvider):
    def lookup(self, uri):
        if urlparse.urlsplit(uri).scheme not in self.backend.uri_schemes:
            return []
        # TODO: actually lookup the stream metadata by getting tags in same
        # way as we do for updating the local library with mopidy.scanner
        # Note that we would only want the stream metadata at this stage,
        # not the currently playing track's.
        return [Track(uri=uri, name=uri)]


class StreamTracklistProvider(base.BaseTracklistProvider):
    def mark(self, tracklist, how, tl_track, **kwargs):
        if not how == "metadata":
            return False
        meta = kwargs['metadata']
        logger.debug("Calling stream's mark function with meta: " + repr(meta))

        track_args = dict()
        album_args = dict()
        artist_args = dict()
        track_args['uri'] = tl_track.track.uri

        if not "title" in meta:
            return False
        track_args['name'] = meta['title']

        artist_args['uri'] = None

        if "artist" in meta:
            artist_args['name'] = meta['artist']
        elif "musicbrainz-sortname" in meta:
            artist_args['name'] = meta['musicbrainz-sortname']
        elif "album-artist" in meta:
            artist_args['name'] = meta['album-artist']
        elif "album-artist-sortname" in meta:
            artist_args['name'] = meta['album-artist-sortname']
        elif "performer" in meta:
            artist_args['name'] = meta['performer']
        elif "composer" in meta:
            artist_args['name'] = meta['composer']
        elif "composer-sortname" in meta:
            artist_args['name'] = meta['composer-sortname']
        else:
            artist_args['name'] = None

        artist_args['musicbrainz_id'] = None

        artist = Artist(**artist_args)
        track_args['artists'] = [artist]

        album_args['uri'] = None
        if "album" in meta:
            album_args['name'] = meta['album']
        elif "album-sortname" in meta:
            album_args['name'] = meta['album-sortname']
        elif "show-name" in meta:
            album_args['name'] = meta['show-name']
        elif "show-sortname" in meta:
            album_args['name'] = meta['show-sortname']

        album_args['artists'] = track_args['artists']

        if "track-count" in meta:
            album_args['num_tracks'] = meta['track-count']

        if 'album-disc-count' in meta:
            album_args['num_discs'] = meta['album-disc-count']

        if 'date' in meta:
            album_args['date'] = meta['date']
        elif 'datetime' in meta:
            album_args['date'] = meta['datetime']

        album_args['musicbrainz_id'] = None
        album_args['images'] = None

        track_args['album'] = Album(album_args)

        if 'track-number' in meta:
            track_args['track_no'] = meta['track-number']
        elif 'show-episode-number' in meta:
            track_args['track_no'] = meta['show-episode-number']

        if 'album-disc-number' in meta:
            track_args['disc_no'] = meta['album-disc-number']
        elif 'show-season-number' in meta:
            track_args['disc_no'] = meta['show-season-number']

        if 'date' in meta:
            track_args['date'] = meta['date']
        elif 'datetime' in meta:
            track_args['date'] = meta['datetime']

        if 'duration' in meta:
            track_args['length'] = meta['duration']

        if 'bitrate' in meta:
            track_args['bitrate'] = meta['bitrate']
        elif 'nominal-bitrate' in meta:
            track_args['bitrate'] = meta['nominal-bitrate']
        elif 'maximum-bitrate' in meta:
            track_args['bitrate'] = meta['maximum-bitrate']
        elif 'minimum-bitrate' in meta:
            track_args['bitrate'] = meta['minimum-bitrate']

        if 'isrc' in meta:
            track_args['musicbrainz_id'] = meta['isrc']
        elif 'serial' in meta:
            track_args['musicbrainz_id'] = meta['serial']

        if 'version' in meta:
            track_args['last_modified'] = meta['version']

        position = tracklist.index(tl_track)
        track=[Track(**track_args)]
        next = tracklist._add(tracks=track, at_position=position)[0]
        listener.CoreListener.send('track_playback_ended',
                    tl_track=tl_track,
                    time_position=self.backend.playback.get_time_position())
        tracklist.core.playback.current_tl_track = next
        listener.CoreListener.send('track_playback_started',
                    tl_track=next)

        return True
