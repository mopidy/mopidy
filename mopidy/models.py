from copy import copy

class Artist(object):
    def __init__(self, uri=None, name=None):
        self._uri = None
        self._name = name

    @property
    def uri(self):
        return self._uri

    @property
    def name(self):
        return self._name


class Album(object):
    def __init__(self, uri=None, name=None, artists=None, num_tracks=0):
        self._uri = uri
        self._name = name
        self._artists = artists or []
        self._num_tracks = num_tracks

    @property
    def uri(self):
        return self._uri

    @property
    def name(self):
        return self._name

    @property
    def artists(self):
        return copy(self._artists)

    @property
    def num_tracks(self):
        return self._num_tracks


class Track(object):
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
        return self._uri

    @property
    def title(self):
        return self._title

    @property
    def artists(self):
        return copy(self._artists)

    @property
    def album(self):
        return self._album

    @property
    def track_no(self):
        return self._track_no

    @property
    def date(self):
        return self._date

    @property
    def length(self):
        return self._length

    @property
    def id(self):
        return self._id

    def mpd_format(self, position=0):
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
        return u', '.join([a.name for a in self.artists])


class Playlist(object):
    def __init__(self, uri=None, name=None, tracks=None):
        self._uri = uri
        self._name = name
        self._tracks = tracks or []

    @property
    def uri(self):
        return self._uri

    @property
    def name(self):
        return self._name

    @property
    def tracks(self):
        return copy(self._tracks)

    @property
    def length(self):
        return len(self._tracks)

    def mpd_format(self, start=0, end=None):
        if end is None:
            end = self.length
        tracks = []
        for track, position in zip(self.tracks, range(start, end)):
            tracks.append(track.mpd_format(position))
        return tracks
