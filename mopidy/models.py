from __future__ import unicode_literals

import json


class ImmutableObject(object):
    """
    Superclass for immutable objects whose fields can only be modified via the
    constructor.

    :param kwargs: kwargs to set as fields on the object
    :type kwargs: any
    """

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key) or callable(getattr(self, key)):
                raise TypeError(
                    '__init__() got an unexpected keyword argument "%s"' %
                    key)
            self.__dict__[key] = value

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super(ImmutableObject, self).__setattr__(name, value)
        raise AttributeError('Object is immutable.')

    def __repr__(self):
        kwarg_pairs = []
        for (key, value) in sorted(self.__dict__.items()):
            if isinstance(value, (frozenset, tuple)):
                value = list(value)
            kwarg_pairs.append('%s=%s' % (key, repr(value)))
        return '%(classname)s(%(kwargs)s)' % {
            'classname': self.__class__.__name__,
            'kwargs': ', '.join(kwarg_pairs),
        }

    def __hash__(self):
        hash_sum = 0
        for key, value in self.__dict__.items():
            hash_sum += hash(key) + hash(value)
        return hash_sum

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self, **values):
        """
        Copy the model with ``field`` updated to new value.

        Examples::

            # Returns a track with a new name
            Track(name='foo').copy(name='bar')
            # Return an album with a new number of tracks
            Album(num_tracks=2).copy(num_tracks=5)

        :param values: the model fields to modify
        :type values: dict
        :rtype: new instance of the model being copied
        """
        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details
        data = {}
        for key in self.__dict__.keys():
            public_key = key.lstrip('_')
            data[str(public_key)] = values.pop(public_key, self.__dict__[key])
        for key in values.keys():
            if hasattr(self, key):
                data[str(key)] = values.pop(key)
        if values:
            raise TypeError(
                'copy() got an unexpected keyword argument "%s"' % key)
        return self.__class__(**data)

    def serialize(self):
        data = {}
        data['__model__'] = self.__class__.__name__
        for key in self.__dict__.keys():
            public_key = key.lstrip('_')
            value = self.__dict__[key]
            if isinstance(value, (set, frozenset, list, tuple)):
                value = [o.serialize() for o in value]
            elif isinstance(value, ImmutableObject):
                value = value.serialize()
            if value:
                data[public_key] = value
        return data


class ModelJSONEncoder(json.JSONEncoder):
    """
    Automatically serialize Mopidy models to JSON.

    Usage::

        >>> import json
        >>> json.dumps({'a_track': Track(name='name')}, cls=ModelJSONEncoder)
        '{"a_track": {"__model__": "Track", "name": "name"}}'

    """
    def default(self, obj):
        if isinstance(obj, ImmutableObject):
            return obj.serialize()
        return json.JSONEncoder.default(self, obj)


def model_json_decoder(dct):
    """
    Automatically deserialize Mopidy models from JSON.

    Usage::

        >>> import json
        >>> json.loads(
        ...     '{"a_track": {"__model__": "Track", "name": "name"}}',
        ...     object_hook=model_json_decoder)
        {u'a_track': Track(artists=[], name=u'name')}

    """
    if '__model__' in dct:
        model_name = dct.pop('__model__')
        cls = globals().get(model_name, None)
        if issubclass(cls, ImmutableObject):
            return cls(**dct)
    return dct


class Artist(ImmutableObject):
    """
    :param uri: artist URI
    :type uri: string
    :param name: artist name
    :type name: string
    :param musicbrainz_id: MusicBrainz ID
    :type musicbrainz_id: string
    """

    #: The artist URI. Read-only.
    uri = None

    #: The artist name. Read-only.
    name = None

    #: The MusicBrainz ID of the artist. Read-only.
    musicbrainz_id = None


class Album(ImmutableObject):
    """
    :param uri: album URI
    :type uri: string
    :param name: album name
    :type name: string
    :param artists: album artists
    :type artists: list of :class:`Artist`
    :param num_tracks: number of tracks in album
    :type num_tracks: integer
    :param date: album release date (YYYY or YYYY-MM-DD)
    :type date: string
    :param musicbrainz_id: MusicBrainz ID
    :type musicbrainz_id: string
    :param images: album image URIs
    :type images: list of strings
    """

    #: The album URI. Read-only.
    uri = None

    #: The album name. Read-only.
    name = None

    #: A set of album artists. Read-only.
    artists = frozenset()

    #: The number of tracks in the album. Read-only.
    num_tracks = 0

    #: The album release date. Read-only.
    date = None

    #: The MusicBrainz ID of the album. Read-only.
    musicbrainz_id = None

    #: The album image URIs. Read-only.
    images = frozenset()

    def __init__(self, *args, **kwargs):
        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details
        self.__dict__[b'artists'] = frozenset(kwargs.pop('artists', []))
        self.__dict__[b'images'] = frozenset(kwargs.pop('images', []))
        super(Album, self).__init__(*args, **kwargs)


class Track(ImmutableObject):
    """
    :param uri: track URI
    :type uri: string
    :param name: track name
    :type name: string
    :param artists: track artists
    :type artists: list of :class:`Artist`
    :param album: track album
    :type album: :class:`Album`
    :param track_no: track number in album
    :type track_no: integer
    :param date: track release date (YYYY or YYYY-MM-DD)
    :type date: string
    :param length: track length in milliseconds
    :type length: integer
    :param bitrate: bitrate in kbit/s
    :type bitrate: integer
    :param musicbrainz_id: MusicBrainz ID
    :type musicbrainz_id: string
    """

    #: The track URI. Read-only.
    uri = None

    #: The track name. Read-only.
    name = None

    #: A set of track artists. Read-only.
    artists = frozenset()

    #: The track :class:`Album`. Read-only.
    album = None

    #: The track number in album. Read-only.
    track_no = 0

    #: The track release date. Read-only.
    date = None

    #: The track length in milliseconds. Read-only.
    length = None

    #: The track's bitrate in kbit/s. Read-only.
    bitrate = None

    #: The MusicBrainz ID of the track. Read-only.
    musicbrainz_id = None

    def __init__(self, *args, **kwargs):
        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details
        self.__dict__[b'artists'] = frozenset(kwargs.pop('artists', []))
        super(Track, self).__init__(*args, **kwargs)


class TlTrack(ImmutableObject):
    """
    A tracklist track. Wraps a regular track and it's tracklist ID.

    The use of :class:`TlTrack` allows the same track to appear multiple times
    in the tracklist.

    This class also accepts it's parameters as positional arguments. Both
    arguments must be provided, and they must appear in the order they are
    listed here.

    This class also supports iteration, so your extract its values like this::

        (tlid, track) = tl_track

    :param tlid: tracklist ID
    :type tlid: int
    :param track: the track
    :type track: :class:`Track`
    """

    #: The tracklist ID. Read-only.
    tlid = None

    #: The track. Read-only.
    track = None

    def __init__(self, *args, **kwargs):
        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details
        if len(args) == 2 and len(kwargs) == 0:
            kwargs[b'tlid'] = args[0]
            kwargs[b'track'] = args[1]
            args = []
        super(TlTrack, self).__init__(*args, **kwargs)

    def __iter__(self):
        return iter([self.tlid, self.track])


class Playlist(ImmutableObject):
    """
    :param uri: playlist URI
    :type uri: string
    :param name: playlist name
    :type name: string
    :param tracks: playlist's tracks
    :type tracks: list of :class:`Track` elements
    :param last_modified: playlist's modification time in UTC
    :type last_modified: :class:`datetime.datetime`
    """

    #: The playlist URI. Read-only.
    uri = None

    #: The playlist name. Read-only.
    name = None

    #: The playlist's tracks. Read-only.
    tracks = tuple()

    #: The playlist modification time in UTC. Read-only.
    #:
    #: :class:`datetime.datetime`, or :class:`None` if unknown.
    last_modified = None

    def __init__(self, *args, **kwargs):
        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details
        self.__dict__[b'tracks'] = tuple(kwargs.pop('tracks', []))
        super(Playlist, self).__init__(*args, **kwargs)

    # TODO: def insert(self, pos, track): ... ?

    @property
    def length(self):
        """The number of tracks in the playlist. Read-only."""
        return len(self.tracks)


class SearchResult(ImmutableObject):
    """
    :param uri: search result URI
    :type uri: string
    :param tracks: matching tracks
    :type tracks: list of :class:`Track` elements
    :param artists: matching artists
    :type artists: list of :class:`Artist` elements
    :param albums: matching albums
    :type albums: list of :class:`Album` elements
    """

    # The search result URI. Read-only.
    uri = None

    # The tracks matching the search query. Read-only.
    tracks = tuple()

    # The artists matching the search query. Read-only.
    artists = tuple()

    # The albums matching the search query. Read-only.
    albums = tuple()

    def __init__(self, *args, **kwargs):
        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details
        self.__dict__[b'tracks'] = tuple(kwargs.pop('tracks', []))
        self.__dict__[b'artists'] = tuple(kwargs.pop('artists', []))
        self.__dict__[b'albums'] = tuple(kwargs.pop('albums', []))
        super(SearchResult, self).__init__(*args, **kwargs)
