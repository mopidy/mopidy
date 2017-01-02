from __future__ import absolute_import, unicode_literals

from mopidy import compat
from mopidy.models import fields
from mopidy.models.immutable import ImmutableObject, ValidatedImmutableObject
from mopidy.models.serialize import ModelJSONEncoder, model_json_decoder

__all__ = [
    'ImmutableObject', 'Ref', 'Image', 'Artist', 'Album', 'track', 'TlTrack',
    'Playlist', 'SearchResult', 'model_json_decoder', 'ModelJSONEncoder',
    'ValidatedImmutableObject']


class Ref(ValidatedImmutableObject):

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
    uri = fields.URI()

    #: The object name. Read-only.
    name = fields.String()

    #: The object type, e.g. "artist", "album", "track", "playlist",
    #: "directory". Read-only.
    type = fields.Identifier()  # TODO: consider locking this down.
    # type = fields.Field(choices=(ALBUM, ARTIST, DIRECTORY, PLAYLIST, TRACK))

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


class Image(ValidatedImmutableObject):

    """
    :param string uri: URI of the image
    :param int width: Optional width of image or :class:`None`
    :param int height: Optional height of image or :class:`None`
    """

    #: The image URI. Read-only.
    uri = fields.URI()

    #: Optional width of the image or :class:`None`. Read-only.
    width = fields.Integer(min=0)

    #: Optional height of the image or :class:`None`. Read-only.
    height = fields.Integer(min=0)


class Artist(ValidatedImmutableObject):

    """
    :param uri: artist URI
    :type uri: string
    :param name: artist name
    :type name: string
    :param sortname: artist name for sorting
    :type sortname: string
    :param musicbrainz_id: MusicBrainz ID
    :type musicbrainz_id: string
    """

    #: The artist URI. Read-only.
    uri = fields.URI()

    #: The artist name. Read-only.
    name = fields.String()

    #: Artist name for better sorting, e.g. with articles stripped
    sortname = fields.String()

    #: The MusicBrainz ID of the artist. Read-only.
    musicbrainz_id = fields.Identifier()


class Album(ValidatedImmutableObject):

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

    .. deprecated:: 1.2
        The ``images`` field is deprecated.
        Use :meth:`mopidy.core.LibraryController.get_images` instead.
    """

    #: The album URI. Read-only.
    uri = fields.URI()

    #: The album name. Read-only.
    name = fields.String()

    #: A set of album artists. Read-only.
    artists = fields.Collection(type=Artist, container=frozenset)

    #: The number of tracks in the album. Read-only.
    num_tracks = fields.Integer(min=0)

    #: The number of discs in the album. Read-only.
    num_discs = fields.Integer(min=0)

    #: The album release date. Read-only.
    date = fields.Date()

    #: The MusicBrainz ID of the album. Read-only.
    musicbrainz_id = fields.Identifier()

    #: The album image URIs. Read-only.
    #:
    #: .. deprecated:: 1.2
    #:     Use :meth:`mopidy.core.LibraryController.get_images` instead.
    images = fields.Collection(type=compat.string_types, container=frozenset)


class Track(ValidatedImmutableObject):

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
    :type composers: list of :class:`Artist`
    :param performers: track performers
    :type performers: list of :class:`Artist`
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
    uri = fields.URI()

    #: The track name. Read-only.
    name = fields.String()

    #: A set of track artists. Read-only.
    artists = fields.Collection(type=Artist, container=frozenset)

    #: The track :class:`Album`. Read-only.
    album = fields.Field(type=Album)

    #: A set of track composers. Read-only.
    composers = fields.Collection(type=Artist, container=frozenset)

    #: A set of track performers`. Read-only.
    performers = fields.Collection(type=Artist, container=frozenset)

    #: The track genre. Read-only.
    genre = fields.String()

    #: The track number in the album. Read-only.
    track_no = fields.Integer(min=0)

    #: The disc number in the album. Read-only.
    disc_no = fields.Integer(min=0)

    #: The track release date. Read-only.
    date = fields.Date()

    #: The track length in milliseconds. Read-only.
    length = fields.Integer(min=0)

    #: The track's bitrate in kbit/s. Read-only.
    bitrate = fields.Integer(min=0)

    #: The track comment. Read-only.
    comment = fields.String()

    #: The MusicBrainz ID of the track. Read-only.
    musicbrainz_id = fields.Identifier()

    #: Integer representing when the track was last modified. Exact meaning
    #: depends on source of track. For local files this is the modification
    #: time in milliseconds since Unix epoch. For other backends it could be an
    #: equivalent timestamp or simply a version counter.
    last_modified = fields.Integer(min=0)


class TlTrack(ValidatedImmutableObject):

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
    tlid = fields.Integer(min=0)

    #: The track. Read-only.
    track = fields.Field(type=Track)

    def __init__(self, *args, **kwargs):
        if len(args) == 2 and len(kwargs) == 0:
            kwargs['tlid'] = args[0]
            kwargs['track'] = args[1]
            args = []
        super(TlTrack, self).__init__(*args, **kwargs)

    def __iter__(self):
        return iter([self.tlid, self.track])


class Playlist(ValidatedImmutableObject):

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
    uri = fields.URI()

    #: The playlist name. Read-only.
    name = fields.String()

    #: The playlist's tracks. Read-only.
    tracks = fields.Collection(type=Track, container=tuple)

    #: The playlist modification time in milliseconds since Unix epoch.
    #: Read-only.
    #:
    #: Integer, or :class:`None` if unknown.
    last_modified = fields.Integer(min=0)

    # TODO: def insert(self, pos, track): ... ?

    @property
    def length(self):
        """The number of tracks in the playlist. Read-only."""
        return len(self.tracks)


class SearchResult(ValidatedImmutableObject):

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

    #: The search result URI. Read-only.
    uri = fields.URI()

    #: The tracks matching the search query. Read-only.
    tracks = fields.Collection(type=Track, container=tuple)

    #: The artists matching the search query. Read-only.
    artists = fields.Collection(type=Artist, container=tuple)

    #: The albums matching the search query. Read-only.
    albums = fields.Collection(type=Album, container=tuple)
