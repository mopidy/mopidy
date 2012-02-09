import datetime as dt
import logging

from spotify import Link, SpotifyError

from mopidy import settings
from mopidy.models import Artist, Album, Track, Playlist

logger = logging.getLogger('mopidy.backends.spotify.translator')

class SpotifyTranslator(object):
    @classmethod
    def to_mopidy_artist(cls, spotify_artist):
        if not spotify_artist.is_loaded():
            return Artist(name=u'[loading...]')
        return Artist(
            uri=str(Link.from_artist(spotify_artist)),
            name=spotify_artist.name()
        )

    @classmethod
    def to_mopidy_album(cls, spotify_album):
        if spotify_album is None or not spotify_album.is_loaded():
            return Album(name=u'[loading...]')
        # TODO pyspotify got much more data on albums than this
        return Album(name=spotify_album.name())

    @classmethod
    def to_mopidy_track(cls, spotify_track):
        uri = str(Link.from_track(spotify_track, 0))
        if not spotify_track.is_loaded():
            return Track(uri=uri, name=u'[loading...]')
        spotify_album = spotify_track.album()
        if (spotify_album is not None and spotify_album.is_loaded()
                and dt.MINYEAR <= int(spotify_album.year()) <= dt.MAXYEAR):
            date = dt.date(spotify_album.year(), 1, 1)
        else:
            date = None
        return Track(
            uri=uri,
            name=spotify_track.name(),
            artists=[cls.to_mopidy_artist(a) for a in spotify_track.artists()],
            album=cls.to_mopidy_album(spotify_track.album()),
            track_no=spotify_track.index(),
            date=date,
            length=spotify_track.duration(),
            bitrate=settings.SPOTIFY_BITRATE,
        )

    @classmethod
    def to_mopidy_playlist(cls, spotify_playlist):
        if not spotify_playlist.is_loaded():
            return Playlist(name=u'[loading...]')
        if spotify_playlist.type() != 'playlist':
            return
        try:
            return Playlist(
                uri=str(Link.from_playlist(spotify_playlist)),
                name=spotify_playlist.name(),
                # FIXME if check on link is a hackish workaround for is_local
                tracks=[cls.to_mopidy_track(t) for t in spotify_playlist
                    if str(Link.from_track(t, 0))],
            )
        except SpotifyError, e:
            logger.warning(u'Failed translating Spotify playlist: %s', e)
