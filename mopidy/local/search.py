from __future__ import absolute_import, unicode_literals

from mopidy.models import SearchResult


def find_exact(tracks, query=None, limit=100, offset=0, uris=None):
    """
    Filter a list of tracks where ``field`` is ``values``.

    :param list tracks: a list of :class:`~mopidy.models.Track`
    :param dict query: one or more field/value pairs to search for
    :param int limit: maximum number of results to return
    :param int offset: offset into result set to use.
    :param uris: zero or more URI roots to limit the search to
    :type uris: list of strings or :class:`None`
    :rtype: :class:`~mopidy.models.SearchResult`
    """
    # TODO Only return results within URI roots given by ``uris``

    if query is None:
        query = {}

    _validate_query(query)

    for (field, values) in query.items():
        # FIXME this is bound to be slow for large libraries
        for value in values:
            if field == 'track_no':
                q = _convert_to_int(value)
            else:
                q = value.strip()

            def uri_filter(t):
                return q == t.uri

            def track_name_filter(t):
                return q == t.name

            def album_filter(t):
                return q == getattr(getattr(t, 'album', None), 'name', None)

            def artist_filter(t):
                return filter(lambda a: q == a.name, t.artists)

            def albumartist_filter(t):
                return any([
                    q == a.name for a in getattr(t.album, 'artists', [])])

            def composer_filter(t):
                return any([q == a.name for a in getattr(t, 'composers', [])])

            def performer_filter(t):
                return any([q == a.name for a in getattr(t, 'performers', [])])

            def track_no_filter(t):
                return q == t.track_no

            def genre_filter(t):
                return (t.genre and q == t.genre)

            def date_filter(t):
                return q == t.date

            def comment_filter(t):
                return q == t.comment

            def any_filter(t):
                return (uri_filter(t) or
                        track_name_filter(t) or
                        album_filter(t) or
                        artist_filter(t) or
                        albumartist_filter(t) or
                        composer_filter(t) or
                        performer_filter(t) or
                        track_no_filter(t) or
                        genre_filter(t) or
                        date_filter(t) or
                        comment_filter(t))

            if field == 'uri':
                tracks = filter(uri_filter, tracks)
            elif field == 'track_name':
                tracks = filter(track_name_filter, tracks)
            elif field == 'album':
                tracks = filter(album_filter, tracks)
            elif field == 'artist':
                tracks = filter(artist_filter, tracks)
            elif field == 'albumartist':
                tracks = filter(albumartist_filter, tracks)
            elif field == 'composer':
                tracks = filter(composer_filter, tracks)
            elif field == 'performer':
                tracks = filter(performer_filter, tracks)
            elif field == 'track_no':
                tracks = filter(track_no_filter, tracks)
            elif field == 'genre':
                tracks = filter(genre_filter, tracks)
            elif field == 'date':
                tracks = filter(date_filter, tracks)
            elif field == 'comment':
                tracks = filter(comment_filter, tracks)
            elif field == 'any':
                tracks = filter(any_filter, tracks)
            else:
                raise LookupError('Invalid lookup field: %s' % field)

    if limit is None:
        tracks = tracks[offset:]
    else:
        tracks = tracks[offset:offset + limit]
    # TODO: add local:search:<query>
    return SearchResult(uri='local:search', tracks=tracks)


def search(tracks, query=None, limit=100, offset=0, uris=None):
    """
    Filter a list of tracks where ``field`` is like ``values``.

    :param list tracks: a list of :class:`~mopidy.models.Track`
    :param dict query: one or more field/value pairs to search for
    :param int limit: maximum number of results to return
    :param int offset: offset into result set to use.
    :param uris: zero or more URI roots to limit the search to
    :type uris: list of strings or :class:`None`
    :rtype: :class:`~mopidy.models.SearchResult`
    """
    # TODO Only return results within URI roots given by ``uris``

    if query is None:
        query = {}

    _validate_query(query)

    for (field, values) in query.items():
        # FIXME this is bound to be slow for large libraries
        for value in values:
            if field == 'track_no':
                q = _convert_to_int(value)
            else:
                q = value.strip().lower()

            def uri_filter(t):
                return bool(t.uri and q in t.uri.lower())

            def track_name_filter(t):
                return bool(t.name and q in t.name.lower())

            def album_filter(t):
                return bool(t.album and t.album.name and
                            q in t.album.name.lower())

            def artist_filter(t):
                return bool(filter(
                    lambda a: bool(a.name and q in a.name.lower()), t.artists))

            def albumartist_filter(t):
                return any([a.name and q in a.name.lower()
                            for a in getattr(t.album, 'artists', [])])

            def composer_filter(t):
                return any([a.name and q in a.name.lower()
                            for a in getattr(t, 'composers', [])])

            def performer_filter(t):
                return any([a.name and q in a.name.lower()
                            for a in getattr(t, 'performers', [])])

            def track_no_filter(t):
                return q == t.track_no

            def genre_filter(t):
                return bool(t.genre and q in t.genre.lower())

            def date_filter(t):
                return bool(t.date and t.date.startswith(q))

            def comment_filter(t):
                return bool(t.comment and q in t.comment.lower())

            def any_filter(t):
                return (uri_filter(t) or
                        track_name_filter(t) or
                        album_filter(t) or
                        artist_filter(t) or
                        albumartist_filter(t) or
                        composer_filter(t) or
                        performer_filter(t) or
                        track_no_filter(t) or
                        genre_filter(t) or
                        date_filter(t) or
                        comment_filter(t))

            if field == 'uri':
                tracks = filter(uri_filter, tracks)
            elif field == 'track_name':
                tracks = filter(track_name_filter, tracks)
            elif field == 'album':
                tracks = filter(album_filter, tracks)
            elif field == 'artist':
                tracks = filter(artist_filter, tracks)
            elif field == 'albumartist':
                tracks = filter(albumartist_filter, tracks)
            elif field == 'composer':
                tracks = filter(composer_filter, tracks)
            elif field == 'performer':
                tracks = filter(performer_filter, tracks)
            elif field == 'track_no':
                tracks = filter(track_no_filter, tracks)
            elif field == 'genre':
                tracks = filter(genre_filter, tracks)
            elif field == 'date':
                tracks = filter(date_filter, tracks)
            elif field == 'comment':
                tracks = filter(comment_filter, tracks)
            elif field == 'any':
                tracks = filter(any_filter, tracks)
            else:
                raise LookupError('Invalid lookup field: %s' % field)

    if limit is None:
        tracks = tracks[offset:]
    else:
        tracks = tracks[offset:offset + limit]
    # TODO: add local:search:<query>
    return SearchResult(uri='local:search', tracks=tracks)


def _validate_query(query):
    for (_, values) in query.items():
        if not values:
            raise LookupError('Missing query')
        for value in values:
            if not value:
                raise LookupError('Missing query')


def _convert_to_int(string):
    try:
        return int(string)
    except ValueError:
        return object()
