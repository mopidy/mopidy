from __future__ import unicode_literals

import urllib
import logging
import re

from mopidy import settings
from mopidy.backends import base
from mopidy.models import Album, SearchResult, Track
from mopidy.utils.path import path_to_uri, uri_to_path

from .translator import convert_mongo_doc_to_track

from pymongo import MongoClient

logger = logging.getLogger('mopidy.backends.mongodb')

def _convert_mongo_resultset_to_tracks( rs ):
    for d in rs:
        yield convert_mongo_doc_to_track( d, settings.LOCAL_MUSIC_PATH )

class MongoDBLibraryProvider(base.BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(MongoDBLibraryProvider, self).__init__(*args, **kwargs)
        mongo = MongoClient( settings.MONGODB_URL )
        self.mongo = mongo.mopidy.music

    def refresh(self, uri=None):
        raise NotImplementedError

    def lookup(self, uri):
        if uri.startswith( "file://" ):
            uri = uri.replace( "file://", "" )

        if uri.startswith( settings.LOCAL_MUSIC_PATH ):
            uri = uri.replace( settings.LOCAL_MUSIC_PATH, "" )

        if uri[ 0 ] == '/':
            uri = uri[ 1 : ]

        try:
            return [ convert_mongo_doc_to_track( self.mongo.find_one( { 'file' : uri } ), settings.LOCAL_MUSIC_PATH ) ]
        except KeyError:
            logger.debug('Failed to lookup %r', uri)
            return []

    def find_exact(self, **query):
        return self._find( exact = True, **query )

    def search(self, **query):
        return self._find( exact = False, **query )

    def _find(self, exact = True, **query):
        self._validate_query(query)
        result_albums = set()
        result_artists = set()
        result_tracks = set()

        for ( field, values ) in query.iteritems():
            if not hasattr( values, '__iter__') :
                values = [ values ]

            for value in values:
                q = value.strip()

                if not exact:
                    q = q.lower()

                if field == 'uri':
                    result_tracks = result_tracks.union( _convert_mongo_resultset_to_tracks( self.mongo.find( { 'file' : 
                        ( uri_to_path( q ) if exact else re.compile( uri_to_path( q ), re.IGNORECASE ) ) } ) ) )
                elif field == 'track':
                    result_tracks = result_tracks.union( _convert_mongo_resultset_to_tracks( self.mongo.find( { 'Title' : 
                        ( q if exact else re.compile( q, re.IGNORECASE ) ) } ) ) )
                elif field == 'album':
                    for t in _convert_mongo_resultset_to_tracks( self.mongo.find( { 'Album' : 
                        ( q if exact else re.compile( q, re.IGNORECASE ) ) } ) ):
                        result_albums.add( t.album )
                        result_tracks.add( t )
                elif field == 'artist':
                    for t in _convert_mongo_resultset_to_tracks( self.mongo.find( { 'Artist' : 
                        ( q if exact else re.compile( q, re.IGNORECASE ) ) } ) ):
                        result_artists |= t.artists
                        result_albums.add( t.album )
                        result_tracks.add( t )
                elif field == 'date':
                    result_tracks = result_tracks.union( _convert_mongo_resultset_to_tracks( self.mongo.find( { 'Year' : 
                        ( int( q ) if exact else re.compile( "^%s" % q, re.IGNORECASE ) ) } ) ) )
                elif field == 'any':
                    result_tracks = result_tracks.union( _convert_mongo_resultset_to_tracks( self.mongo.find( { 'file' : 
                        ( urllib.quote( q ) if exact else re.compile( urllib.quote( q ), re.IGNORECASE ) ) } ) ) )
                    result_tracks = result_tracks.union( _convert_mongo_resultset_to_tracks( self.mongo.find( { 'Title' : 
                        ( q if exact else re.compile( q, re.IGNORECASE ) ) } ) ) )

                    for t in _convert_mongo_resultset_to_tracks( self.mongo.find( { 'Album' : 
                        ( q if exact else re.compile( q, re.IGNORECASE ) ) } ) ):
                        result_albums.add( t.album )
                        result_tracks.add( t )

                    for t in _convert_mongo_resultset_to_tracks( self.mongo.find( { 'Artist' : 
                        ( q if exact else re.compile( q, re.IGNORECASE ) ) } ) ):
                        result_artists |= t.artists
                        result_albums.add( t.album )
                        result_tracks.add( t )

                    result_tracks = result_tracks.union( _convert_mongo_resultset_to_tracks( self.mongo.find( { 'Year' : 
                        ( int( q ) if exact else re.compile( "^%s" % q, re.IGNORECASE ) ) } ) ) )
                else:
                    raise LookupError('Invalid lookup field: %s' % field)

        return SearchResult( uri = 'file:search', artists = result_artists, albums = result_albums, tracks = result_tracks )

    def _validate_query(self, query):
        for (_, values) in query.iteritems():
            if not values:
                raise LookupError('Missing query')
            for value in values:
                if not value:
                    raise LookupError('Missing query')

