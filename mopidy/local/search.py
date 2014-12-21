from __future__ import absolute_import, unicode_literals

from mopidy.models import Album, SearchResult,Track,Artist,Album


def find_exact(tracks, query=None, uris=None):
    # TODO Only return results within URI roots given by ``uris``

    if query is None:
        query = {}

    _validate_query(query)

    for (field, values) in query.items():
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

    for (field, values) in query.items():
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

def advanced_search(tracks,artists,albums,query=None,uris=None,exact=False,returnType=None):
# if returntype = none, search for all things that match (tracks, artists, albums)
# for specific return types, either:
#    if an artist search has either trackname or trackno searches, then first filter tracks, and use that 
#    to get a set of artists
#    if artist search has album search then filter albums to get set of artists
#    use intersection of these to filter out the right thing
# 
#    if album search has trackname/trackno, filter tracks, use that to get list of possible albums then apply 
#    any album filters

    # we only do a full track scan if we really need to, otherwise we just scan artists/albums
    # we need a full track query if we are:
    # 1)Returning a list of tracks (or everything, returntype==None)
    # 2)Returning artists or albums, but the query includes trackname or similar
    # otherwise we can skip the track query

    if query==None or len(query)==0:
      #if we have an empty query then only pass out what is needed, and do it straight away
        if returnType==Artist:
            return SearchResult(artists=artists)
        elif returnType==Track:
            return SearchResult(tracks=tracks)
        elif returnType==Album:
            return SearchResult(albums=albums)       
        elif returnType==None:
            return SearchResult(artists=artists,tracks=tracks,albums=albums)
    # when we have just 'query album, artist = blah', do this quickly, rather than searching all tracks
    if returnType==Album and query.keys()==['artist'] or query.keys()==['albumartist']:
        nameQuery=query.values()[0]
        if exact:
            albumResults=albums
            for q in nameQuery:
                q=q.lower().strip()
                albumartist_filter = lambda al: any([
                    ar.name and q==ar.name.lower()
                    for ar in al.artists])
                albumResults=filter(albumartist_filter,albumResults)
        else:
            albumResults=albums
            for q in nameQuery:
                q=q.lower().strip()
                albumartist_filter = lambda al: any([
                    ar.name and q in ar.name.lower()
                    for ar in al.artists])
                albumResults=filter(albumartist_filter,albumResults)
        
    if not exact:
        trackResults=search(tracks,query,uris).tracks
    else:
        trackResults=find_exact(tracks,query,uris).tracks    

    artistResults=None
    albumResults=None
    if returnType==None or returnType==Artist:
      # get list of artists from these tracks
      # we need to filter it down in the case that our query is on
      # artist name, so that if an artist is on a track with another
      # the other one doesn't get returned
      artistResults={}
      for track in trackResults:
          for artist in track.artists:
            artistResults[artist.uri]=artist
      artistResults=artistResults.values()
    if returnType==None or returnType==Album:
        albumResults={}
        for track in trackResults:
            albumResults[track.album.uri]=track.album
        albumResults=albumResults.values()
    #only return the type of results that were asked for, even if we had to do a track search to find them
    if returnType==Album:
        trackResults=None
        artistResults=None
    elif returnType==Artist:
        trackResults=None
        albumResults=None
    elif returnType==Track:
        artistResults=None
        albumResults=None        
    return SearchResult(tracks=trackResults,artists=artistResults,albums=albumResults)
    

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
