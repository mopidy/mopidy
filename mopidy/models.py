from copy import copy

class Artist(object):
    """
    :param uri: artist URI
    :type uri: string
    :param name: artist name
    :type name: string
    """

    def __init__(self, uri=None, name=None):
        self._uri = None
        self._name = name

    @property
    def uri(self):
        """The artist URI. Read-only."""
        return self._uri

    @property
    def name(self):
        """The artist name. Read-only."""
        return self._name


class Album(object):
    """
    :param uri: album URI
    :type uri: string
    :param name: album name
    :type name: string
    :param artists: album artists
    :type artists: list of :class:`Artist`
    :param num_tracks: number of tracks in album
    :type num_tracks: integer
    """

    def __init__(self, uri=None, name=None, artists=None, num_tracks=0):
        self._uri = uri
        self._name = name
        self._artists = artists or []
        self._num_tracks = num_tracks

    @property
    def uri(self):
        """The album URI. Read-only."""
        return self._uri

    @property
    def name(self):
        """The album name. Read-only."""
        return self._name

    @property
    def artists(self):
        """List of :class:`Artist` elements. Read-only."""
        return copy(self._artists)

    @property
    def num_tracks(self):
        """The number of tracks in the album. Read-only."""
        return self._num_tracks


class Track(object):
    """
    :param uri: track URI
    :type uri: string
    :param title: track title
    :type title: string
    :param artists: track artists
    :type artists: list of :class:`Artist`
    :param album: track album
    :type album: :class:`Album`
    :param track_no: track number in album
    :type track_no: integer
    :param date: track release date
    :type date: :class:`datetime.date`
    :param length: track length in milliseconds
    :type length: integer
    :param id: track ID (unique and non-changing as long as the process lives)
    :type id: integer
    """

    def __init__(self, uri=None, title=None, artists=None, album=None,
            track_no=0, date=None, length=None, id=None):
        self._uri = uri
        self._title = title
        self._artists = artists or []
        self._album = album
        self._track_no = track_no
        self._date = date
        self._length = length
        self._id = id

    @property
    def uri(self):
        """The track URI. Read-only."""
        return self._uri

    @property
    def title(self):
        """The track title. Read-only."""
        return self._title

    @property
    def artists(self):
        """List of :class:`Artist`. Read-only."""
        return copy(self._artists)

    @property
    def album(self):
        """The track :class:`Album`. Read-only."""
        return self._album

    @property
    def track_no(self):
        """The track number in album. Read-only."""
        return self._track_no

    @property
    def date(self):
        """The track release date. Read-only."""
        return self._date

    @property
    def length(self):
        """The track length in milliseconds. Read-only."""
        return self._length

    @property
    def id(self):
        """The track ID. Read-only."""
        return self._id

    def mpd_format(self, position=0):
        """
        Format track for output to MPD client.

        :param position: track's position in playlist
        :type position: integer
        :rtype: list of two-tuples
        """
        return [
            ('file', self.uri),
            ('Time', self.length // 1000),
            ('Artist', self.mpd_format_artists()),
            ('Title', self.title),
            ('Album', self.album.name),
            ('Track', '%d/%d' % (self.track_no, self.album.num_tracks)),
            ('Date', self.date),
            ('Pos', position),
            ('Id', self.id),
        ]

    def mpd_format_artists(self):
        """
        Format track artists for output to MPD client.

        :rtype: string
        """
        return u', '.join([a.name for a in self.artists])


class Playlist(object):
    """
        :param uri: playlist URI
        :type uri: string
        :param name: playlist name
        :type name: string
        :param tracks: playlist's tracks
        :type tracks: list of :class:`Track` elements
    """

    def __init__(self, uri=None, name=None, tracks=None):
        self._uri = uri
        self._name = name
        self._tracks = tracks or []

    @property
    def uri(self):
        """The playlist URI. Read-only."""
        return self._uri

    @property
    def name(self):
        """The playlist name. Read-only."""
        return self._name

    @property
    def tracks(self):
        """List of :class:`Track` elements. Read-only."""
        return copy(self._tracks)

    @property
    def length(self):
        """The number of tracks in the playlist. Read-only."""
        return len(self._tracks)

    def mpd_format(self, start=0, end=None):
        """
        Format playlist for output to MPD client.

        :rtype: list of lists of two-tuples
        """
        if end is None:
            end = self.length
        tracks = []
        for track, position in zip(self.tracks, range(start, end)):
            tracks.append(track.mpd_format(position))
        return tracks
