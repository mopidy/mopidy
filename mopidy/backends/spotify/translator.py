from __future__ import unicode_literals

from spotify import Link

from mopidy import settings
from mopidy.models import Artist, Album, Track, Playlist


def to_mopidy_artist(spotify_artist):
    if spotify_artist is None:
        return
    uri = str(Link.from_artist(spotify_artist))
    if not spotify_artist.is_loaded():
        return Artist(uri=uri, name='[loading...]')
    return Artist(uri=uri, name=spotify_artist.name())


def to_mopidy_album(spotify_album):
    if spotify_album is None:
        return
    uri = str(Link.from_album(spotify_album))
    if not spotify_album.is_loaded():
        return Album(uri=uri, name='[loading...]')
    return Album(
        uri=uri,
        name=spotify_album.name(),
        artists=[to_mopidy_artist(spotify_album.artist())],
        date=spotify_album.year())


def to_mopidy_track(spotify_track):
    if spotify_track is None:
        return
    uri = str(Link.from_track(spotify_track, 0))
    if not spotify_track.is_loaded():
        return Track(uri=uri, name='[loading...]')
    spotify_album = spotify_track.album()
    if spotify_album is not None and spotify_album.is_loaded():
        date = spotify_album.year()
    else:
        date = None
    return Track(
        uri=uri,
        name=spotify_track.name(),
        artists=[to_mopidy_artist(a) for a in spotify_track.artists()],
        album=to_mopidy_album(spotify_track.album()),
        track_no=spotify_track.index(),
        date=date,
        length=spotify_track.duration(),
        bitrate=settings.SPOTIFY_BITRATE)


def to_mopidy_playlist(spotify_playlist):
    if spotify_playlist is None or spotify_playlist.type() != 'playlist':
        return
    uri = str(Link.from_playlist(spotify_playlist))
    if not spotify_playlist.is_loaded():
        return Playlist(uri=uri, name='[loading...]')
    if not spotify_playlist.name():
        # Other user's "starred" playlists isn't handled properly by pyspotify
        # See https://github.com/mopidy/pyspotify/issues/81
        return
    return Playlist(
        uri=uri,
        name=spotify_playlist.name(),
        tracks=[
            to_mopidy_track(spotify_track)
            for spotify_track in spotify_playlist
            if not spotify_track.is_local()])
