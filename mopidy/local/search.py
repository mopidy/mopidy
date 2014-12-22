from __future__ import absolute_import, unicode_literals

from mopidy.models import Album, SearchResult,Track,Artist,Album

from urllib import quote_plus


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

def make_safe(unicodeString):
    if unicodeString==None:
        unicodeString=""
    return quote_plus(unicodeString.encode("utf-8"))

def makeSQL(variables,table,query,exact,search_keys,distinct,limit,offset,orderby=None):
    allfields = search_keys.values()
    allfields.remove("any")
    queryVars=[]
    if exact:
        sql="select "
        if distinct:
            sql+="distinct "
        sql+=','.join(variables)
        sql+=" from tracks "        
        for key,values in query.items():
            if type(values)!=type([]):
                values=[values]
            if search_keys.has_key(key):
                searchkey=search_keys[key]
                for value in values:
                    if len(queryVars)!=0:
                        sql+="and "
                    else:
                        sql+="where "
                    if searchkey=="any":
                        sql+="? in ("+",".join(allfields)+") "
                    else:
                        sql+=searchkey+"=? "
                    queryVars.append(value)
    else:
#        sql=""
#        for key,values in query.items():            
#            if search_keys.has_key(key):
#                searchkey=search_keys[key]
#                if type(values)!=type([]):
#                    values=[values]
#                for value in values:
#                    if len(queryVars)!=0:
#                        sql+="intersect "
#                    sql+="select "
#                    if distinct:
#                        sql+="distinct "
#                    sql+=','.join(variables)
#                    sql+=" from tracks_fts where "        
#                    if searchkey=="any":
#                        sql+="tracks_fts match ? "
#                    else:
#                        sql+="%s match ? "%searchkey
#                    queryVars.append(value)
        sql="select "
        if distinct:
            sql+="distinct "
        sql+=','.join(variables)
        sql+=" from tracks "        
        for key,values in query.items():
            if type(values)!=type([]):
                values=[values]
            if search_keys.has_key(key):
                searchkey=search_keys[key]
                for value in values:
                    if len(queryVars)!=0:
                        sql+="and "
                    else:
                        sql+="where "
                    if searchkey=="any":
                        sql+="("
                        for af in allfields:
                          sql+=af+" like ? or "
                          queryVars.append("%"+value+"%")
                        sql=sql[:-3]
                        sql+=")"
                    else:
                        sql+=searchkey+" like ? "
                        queryVars.append("%"+value+"%")

    if orderby!=None:
        sql+=orderby+" "
    if limit!=0:
        sql+=" limit %d offset %d"%(limit,offset)
    return sql,queryVars
    
def make_artist_list(name):
    if name==None:
        return None
    else:
        return [Artist(name=name,uri="local:directory:type=artist/"+make_safe(name))]

def make_album_result(row):        
    albumURIArtist=row[b"album_artist"]
    if albumURIArtist and len(albumURIArtist)>0:
        albumArtist=make_artist_list(albumURIArtist)
    else:
        albumArtist=None
        albumURIArtist=row[b'artist_name']
    # make album    
    return Album(
        uri="local:directory:type=artist/"+make_safe(albumURIArtist)+"/"+make_safe(row[b"album_name"]),
        name=row[b'album_name'],
        artists=albumArtist,
        date=row[b'date'],
        num_tracks=row[b'num_tracks'])
    
    
def make_track_result(row):
    album=make_album_result(row)
    # make track
    return Track(
        uri=row[b'uri'],
        album=album,
        name=row[b'name'],
        artists=make_artist_list(row[b'artist_name']),
        last_modified=row[b'last_modified'],
        track_no=row[b'track_no'],
        genre=row[b'genre'],
        date=row[b'date'],
        length=row[b'length'],
        performers=make_artist_list(row[b'performer']),
        composers=make_artist_list(row[b'composer']),
        comment=row[b'comment'])
    
def advanced_search_sql(db,query,uris,exact,returnType,limit,offset):
    search_keys={
    "uri":"uri",
    "artist":"artist_name",
    "date":"date",
    "track_name":"name",
    "track_no":"track_no",
    "num_tracks":"num_tracks",
    "genre":"genre",
    "album":"album_name",
    "albumartist":"album_artist",
    "performer":"performer",
    "composer":"composer",
    "comment":"comment",
    "any":"any"}

    for key,values in query.items():
        if not search_keys.has_key(key):
            raise LookupError('Invalid lookup field: %s' % key)
        if len(values)==0:
            raise LookupError('Empty lookup field: %s' % key)
        for val in values:
            if len(val)==0:
                raise LookupError('Empty lookup field: %s' % key)
        

    trackResults=None
    artistResults=None
    albumResults=None
    whereKeys=[]
    whereArgs=[]
    if exact:
        table="tracks"
    else:
        table="tracks_fts"

    if returnType==Album:
      sqlquery,whereArgs=makeSQL(["album_name","artist_name","num_tracks","date","album_artist"],table,query,exact,search_keys,True,limit,offset)
      albumResults=[]
      for row in db.execute(sqlquery,whereArgs):
        albumResults.append(make_album_result(row))
        #Album(uri="local:directory:type=artist/"+make_safe(row[b'artist_name'])+"/"+make_safe(row[b'album_name']),name=row[b'album_name'],artists=[Artist(uri="local:directory:type=artist/"+make_safe(row[b'artist_name']),name=row[b'artist_name'])],num_tracks=row[b'num_tracks'],date=row[b'date']))
    if returnType==Artist:
      sqlquery,whereArgs=makeSQL(["artist_name"],table,query,exact,search_keys,True,limit,offset)
      artistResults=[]
      for row in db.execute(sqlquery,whereArgs):
        artistResults.append(Artist(name=row[0],uri="local:directory:type=artist/"+make_safe(row[0]) ))      
    if returnType==Track or returnType==None:
        if returnType==None:
            artistResults=set()
            albumResults=set()
        trackResults=[]
        sqlquery,whereArgs=makeSQL(["*"],table,query,exact,search_keys,True,limit,offset,"order by artist_name,album_name,track_no asc")
        for row in db.execute(sqlquery,whereArgs):
            track=make_track_result(row)
            trackResults.append(track)
            if returnType==None:
                albumResults.add(track.album)
                artistResults|=track.artists

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
