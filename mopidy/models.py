from __future__ import absolute_import, unicode_literals

import json

# TODO: split into base models, serialization and fields?


class Field(object):
    def __init__(self, default=None, type=None, choices=None):
        """
        Base field for use in :class:`ImmutableObject`. These fields are
        responsible type checking and other data sanitation in our models.

        For simplicity fields use the Python descriptor protocol to store the
        values in the instance dictionary. Also note that fields are mutable if
        the object they are attached to allow it.

        Default values will be validated with the exception of :class:`None`.

        :param default: default value for field
        :param type: if set the field value must be of this type
        :param choices: if set the field value must be one of these
        """
        self._name = None  # Set by FieldOwner
        self._choices = choices
        self._default = default
        self._type = type

        if self._default is not None:
            self.validate(self._default)

    def validate(self, value):
        """Validate and possibly modify the field value before assignment"""
        if self._type and not isinstance(value, self._type):
            raise TypeError('Expected %s to be a %s, not %r' %
                            (self._name, self._type, value))
        if self._choices and value not in self._choices:
            raise TypeError('Expected %s to be a one of %s, not %r' %
                            (self._name, self._choices, value))
        return value

    def __get__(self, instance, owner):
        if not instance:
            return self
        return instance.__dict__.get(self._name, self._default)

    def __set__(self, instance, value):
        if value is not None:
            value = self.validate(value)

        if value is None or value == self._default:
            self.__delete__(instance)
        else:
            instance.__dict__[self._name] = value

    def __delete__(self, instance):
        instance.__dict__.pop(self._name, None)


class String(Field):
    def __init__(self, default=None):
        """
        Specialized :class:`Field` which is wired up for bytes and unicode.

        :param default: default value for field
        """
        # TODO: normalize to unicode?
        # TODO: only allow unicode?
        # TODO: disallow empty strings?
        super(String, self).__init__(type=basestring, default=default)


class Integer(Field):
    def __init__(self, default=None, min=None, max=None):
        """
        :class:`Field` for storing integer numbers.

        :param default: default value for field
        :param min: if set the field value larger or equal to this value
        :param max: if set the field value smaller or equal to this value
        """
        self._min = min
        self._max = max
        super(Integer, self).__init__(type=(int, long), default=default)

    def validate(self, value):
        value = super(Integer, self).validate(value)
        if self._min is not None and value < self._min:
            raise ValueError('Expected %s to be at least %d, not %d' %
                             (self._name, self._min, value))
        if self._max is not None and value > self._max:
            raise ValueError('Expected %s to be at most %d, not %d' %
                             (self._name, self._max, value))
        return value


class Collection(Field):
    def __init__(self, type, container=tuple):
        """
        :class:`Field` for storing collections of a given type.

        :param type: all items stored in the collection must be of this type
        :param container: the type to store the items in
        """
        super(Collection, self).__init__(type=type, default=container())

    def validate(self, value):
        if isinstance(value, basestring):
            raise TypeError('Expected %s to be a collection of %s, not %r'
                            % (self._name, self._type.__name__, value))
        for v in value:
            if not isinstance(v, self._type):
                raise TypeError('Expected %s to be a collection of %s, not %r'
                                % (self._name, self._type.__name__, value))
        return self._default.__class__(value) or None


class FieldOwner(type):
    """Helper to automatically assign field names to descriptors."""
    def __new__(cls, name, bases, attrs):
        attrs['_fields'] = []
        for key, value in attrs.items():
            if isinstance(value, Field):
                attrs['_fields'].append(key)
                value._name = key
        attrs['_fields'].sort()
        return super(FieldOwner, cls).__new__(cls, name, bases, attrs)


class ImmutableObject(object):

    """
    Superclass for immutable objects whose fields can only be modified via the
    constructor. Fields should be :class:`Field` instances to ensure type
    safety in our models.

    :param kwargs: kwargs to set as fields on the object
    :type kwargs: any
    """

    __metaclass__ = FieldOwner

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            if key not in self._fields:
                raise TypeError(
                    '__init__() got an unexpected keyword argument "%s"' %
                    key)
            super(ImmutableObject, self).__setattr__(key, value)

    def __setattr__(self, name, value):
        raise AttributeError('Object is immutable.')

    def __delattr__(self, name):
        raise AttributeError('Object is immutable.')

    def __repr__(self):
        kwarg_pairs = []
        for (key, value) in sorted(self.__dict__.items()):
            if isinstance(value, (frozenset, tuple)):
                if not value:
                    continue
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
        other = self.__class__()
        other.__dict__.update(self.__dict__)
        for key, value in values.items():
            if key not in self._fields:
                raise TypeError(
                    'copy() got an unexpected keyword argument "%s"' % key)
            super(ImmutableObject, other).__setattr__(key, value)
        return other

    def serialize(self):
        data = {}
        data['__model__'] = self.__class__.__name__
        for key, value in self.__dict__.items():
            if isinstance(value, (set, frozenset, list, tuple)):
                value = [
                    v.serialize() if isinstance(v, ImmutableObject) else v
                    for v in value]
            elif isinstance(value, ImmutableObject):
                value = value.serialize()
            if not (isinstance(value, list) and len(value) == 0):
                data[key] = value
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
            kwargs = {}
            for key, value in dct.items():
                kwargs[key] = value
            return cls(**kwargs)
    return dct


class Ref(ImmutableObject):

    """
    Model to represent URI references with a human friendly name and type
    attached. This is intended for use a lightweight object "free" of metadata
    that can be passed around instead of using full blown models.

    :param uri: object URI
    :type uri: string
    :param name: object name
    :type name: string
    :param type: object type
    :type type: string
    """

    #: The object URI. Read-only.
    uri = String()

    #: The object name. Read-only.
    name = String()

    #: Constant used for comparison with the :attr:`type` field.
    ALBUM = 'album'

    #: Constant used for comparison with the :attr:`type` field.
    ARTIST = 'artist'

    #: Constant used for comparison with the :attr:`type` field.
    DIRECTORY = 'directory'

    #: Constant used for comparison with the :attr:`type` field.
    PLAYLIST = 'playlist'

    #: Constant used for comparison with the :attr:`type` field.
    TRACK = 'track'

    #: The object type, e.g. "artist", "album", "track", "playlist",
    #: "directory". Read-only.
    type = Field(choices=(ALBUM, ARTIST, DIRECTORY, PLAYLIST, TRACK))

    @classmethod
    def album(cls, **kwargs):
        """Create a :class:`Ref` with ``type`` :attr:`ALBUM`."""
        kwargs['type'] = Ref.ALBUM
        return cls(**kwargs)

    @classmethod
    def artist(cls, **kwargs):
        """Create a :class:`Ref` with ``type`` :attr:`ARTIST`."""
        kwargs['type'] = Ref.ARTIST
        return cls(**kwargs)

    @classmethod
    def directory(cls, **kwargs):
        """Create a :class:`Ref` with ``type`` :attr:`DIRECTORY`."""
        kwargs['type'] = Ref.DIRECTORY
        return cls(**kwargs)

    @classmethod
    def playlist(cls, **kwargs):
        """Create a :class:`Ref` with ``type`` :attr:`PLAYLIST`."""
        kwargs['type'] = Ref.PLAYLIST
        return cls(**kwargs)

    @classmethod
    def track(cls, **kwargs):
        """Create a :class:`Ref` with ``type`` :attr:`TRACK`."""
        kwargs['type'] = Ref.TRACK
        return cls(**kwargs)


class Image(ImmutableObject):

    """
    :param string uri: URI of the image
    :param int width: Optional width of image or :class:`None`
    :param int height: Optional height of image or :class:`None`
    """

    #: The image URI. Read-only.
    uri = String()

    #: Optional width of the image or :class:`None`. Read-only.
    width = Integer(min=0)

    #: Optional height of the image or :class:`None`. Read-only.
    height = Integer(min=0)


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
    uri = String()

    #: The artist name. Read-only.
    name = String()

    #: The MusicBrainz ID of the artist. Read-only.
    musicbrainz_id = String()


class Album(ImmutableObject):

    """
    :param uri: album URI
    :type uri: string
    :param name: album name
    :type name: string
    :param artists: album artists
    :type artists: list of :class:`Artist`
    :param num_tracks: number of tracks in album
    :type num_tracks: integer or :class:`None` if unknown
    :param num_discs: number of discs in album
    :type num_discs: integer or :class:`None` if unknown
    :param date: album release date (YYYY or YYYY-MM-DD)
    :type date: string
    :param musicbrainz_id: MusicBrainz ID
    :type musicbrainz_id: string
    :param images: album image URIs
    :type images: list of strings
    """

    #: The album URI. Read-only.
    uri = String()

    #: The album name. Read-only.
    name = String()

    #: A set of album artists. Read-only.
    artists = Collection(type=Artist, container=frozenset)

    #: The number of tracks in the album. Read-only.
    num_tracks = Integer(min=0)

    #: The number of discs in the album. Read-only.
    num_discs = Integer(min=0)

    #: The album release date. Read-only.
    date = String()  # TODO: add date type

    #: The MusicBrainz ID of the album. Read-only.
    musicbrainz_id = String()

    #: The album image URIs. Read-only.
    images = Collection(type=basestring, container=frozenset)
    # XXX If we want to keep the order of images we shouldn't use frozenset()
    # as it doesn't preserve order. I'm deferring this issue until we got
    # actual usage of this field with more than one image.


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
    :param composers: track composers
    :type composers: string
    :param performers: track performers
    :type performers: string
    :param genre: track genre
    :type genre: string
    :param track_no: track number in album
    :type track_no: integer or :class:`None` if unknown
    :param disc_no: disc number in album
    :type disc_no: integer or :class:`None` if unknown
    :param date: track release date (YYYY or YYYY-MM-DD)
    :type date: string
    :param length: track length in milliseconds
    :type length: integer or :class:`None` if there is no duration
    :param bitrate: bitrate in kbit/s
    :type bitrate: integer
    :param comment: track comment
    :type comment: string
    :param musicbrainz_id: MusicBrainz ID
    :type musicbrainz_id: string
    :param last_modified: Represents last modification time
    :type last_modified: integer or :class:`None` if unknown
    """

    #: The track URI. Read-only.
    uri = String()

    #: The track name. Read-only.
    name = String()

    #: A set of track artists. Read-only.
    artists = Collection(type=Artist, container=frozenset)

    #: The track :class:`Album`. Read-only.
    album = Field(type=Album)

    #: A set of track composers. Read-only.
    composers = Collection(type=Artist, container=frozenset)

    #: A set of track performers`. Read-only.
    performers = Collection(type=Artist, container=frozenset)

    #: The track genre. Read-only.
    genre = String()

    #: The track number in the album. Read-only.
    track_no = Integer(min=0)

    #: The disc number in the album. Read-only.
    disc_no = Integer(min=0)

    #: The track release date. Read-only.
    date = String()  # TODO: add date type

    #: The track length in milliseconds. Read-only.
    length = Integer(min=0)

    #: The track's bitrate in kbit/s. Read-only.
    bitrate = Integer(min=0)

    #: The track comment. Read-only.
    comment = String()

    #: The MusicBrainz ID of the track. Read-only.
    musicbrainz_id = String()

    #: Integer representing when the track was last modified. Exact meaning
    #: depends on source of track. For local files this is the modification
    #: time in milliseconds since Unix epoch. For other backends it could be an
    #: equivalent timestamp or simply a version counter.
    last_modified = Integer(min=0)


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
    tlid = Integer(min=0)

    #: The track. Read-only.
    track = Field(type=Track)

    def __init__(self, *args, **kwargs):
        if len(args) == 2 and len(kwargs) == 0:
            kwargs['tlid'] = args[0]
            kwargs['track'] = args[1]
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
    :param last_modified:
        playlist's modification time in milliseconds since Unix epoch
    :type last_modified: int
    """

    #: The playlist URI. Read-only.
    uri = String()

    #: The playlist name. Read-only.
    name = String()

    #: The playlist's tracks. Read-only.
    tracks = Collection(type=Track, container=tuple)

    #: The playlist modification time in milliseconds since Unix epoch.
    #: Read-only.
    #:
    #: Integer, or :class:`None` if unknown.
    last_modified = Integer(min=0)

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
    uri = String()

    # The tracks matching the search query. Read-only.
    tracks = Collection(type=Track, container=tuple)

    # The artists matching the search query. Read-only.
    artists = Collection(type=Artist, container=tuple)

    # The albums matching the search query. Read-only.
    albums = Collection(type=Album, container=tuple)
