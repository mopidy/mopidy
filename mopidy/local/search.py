from __future__ import unicode_literals

from mopidy.models import Album, SearchResult


def find_exact(tracks, query=None, uris=None):
    # TODO Only return results within URI roots given by ``uris``

    if query is None:
        query = {}

    _validate_query(query)

    for (field, values) in query.iteritems():
        if not hasattr(values, '__iter__'):
            values = [values]
        # FIXME this is bound to be slow for large libraries
        for value in values:
            if field == 'track_no':
                q = _convert_to_int(value)
            else:
                q = value.strip()

            uri_filter = lambda t: q == t.uri
            track_name_filter = lambda t: q == t.name
            album_filter = lambda t: q == getattr(t, 'album', Album()).name
            artist_filter = lambda t: filter(
                lambda a: q == a.name, t.artists)
            albumartist_filter = lambda t: any([
                q == a.name
                for a in getattr(t.album, 'artists', [])])
            composer_filter = lambda t: any([
                q == a.name
                for a in getattr(t, 'composers', [])])
            performer_filter = lambda t: any([
                q == a.name
                for a in getattr(t, 'performers', [])])
            track_no_filter = lambda t: q == t.track_no
            genre_filter = lambda t: t.genre and q == t.genre
            date_filter = lambda t: q == t.date
            comment_filter = lambda t: q == t.comment
            any_filter = lambda t: (
                uri_filter(t) or
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

    # TODO: add local:search:<query>
    return SearchResult(uri='local:search', tracks=tracks)


def search(tracks, query=None, uris=None):
    # TODO Only return results within URI roots given by ``uris``

    if query is None:
        query = {}

    _validate_query(query)

    for (field, values) in query.iteritems():
        if not hasattr(values, '__iter__'):
            values = [values]
        # FIXME this is bound to be slow for large libraries
        for value in values:
            if field == 'track_no':
                q = _convert_to_int(value)
            else:
                q = value.strip().lower()

            uri_filter = lambda t: bool(t.uri and q in t.uri.lower())
            track_name_filter = lambda t: bool(t.name and q in t.name.lower())
            album_filter = lambda t: bool(
                t.album and t.album.name and q in t.album.name.lower())
            artist_filter = lambda t: bool(filter(
                lambda a: bool(a.name and q in a.name.lower()), t.artists))
            albumartist_filter = lambda t: any([
                a.name and q in a.name.lower()
                for a in getattr(t.album, 'artists', [])])
            composer_filter = lambda t: any([
                a.name and q in a.name.lower()
                for a in getattr(t, 'composers', [])])
            performer_filter = lambda t: any([
                a.name and q in a.name.lower()
                for a in getattr(t, 'performers', [])])
            track_no_filter = lambda t: q == t.track_no
            genre_filter = lambda t: bool(t.genre and q in t.genre.lower())
            date_filter = lambda t: bool(t.date and t.date.startswith(q))
            comment_filter = lambda t: bool(
                t.comment and q in t.comment.lower())
            any_filter = lambda t: (
                uri_filter(t) or
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
    # TODO: add local:search:<query>
    return SearchResult(uri='local:search', tracks=tracks)


def _validate_query(query):
    for (_, values) in query.iteritems():
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
