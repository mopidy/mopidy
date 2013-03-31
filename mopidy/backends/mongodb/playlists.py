from __future__ import unicode_literals

import glob
import logging
import os
import shutil
import urllib

from mopidy import settings
from mopidy.backends import base, listener
from mopidy.models import Playlist
from mopidy.utils import formatting, path

from pymongo import MongoClient

from .translator import convert_mongo_doc_to_track

logger = logging.getLogger('mopidy.backends.mongodb')

class MongoDBPlaylistsProvider(base.BasePlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(MongoDBPlaylistsProvider, self).__init__(*args, **kwargs)
        mongo = MongoClient( settings.MONGODB_URL )
        mongo.write_concern = { 'w' : 1 }
        self.mongo = mongo.mopidy.playlists

    def create(self, name):
        name = formatting.slugify(name)
        playlist = Playlist(uri=urllib.quote( name ), name=name)
        return self.save(playlist)

    @property
    def playlists(self):
        """
        Currently available playlists.

        Read/write. List of :class:`mopidy.models.Playlist`.
        """
        playlists = []

        for doc in self.mongo.find():
            for i in range( len( doc[ "tracks" ] ) ):
                doc[ "tracks" ][ i ] = self.backend.library.lookup( doc[ "tracks" ][ i ][ "file" ] )
                doc[ "tracks" ][ i ] = doc[ "tracks" ][ i ][ 0 ]

            playlists.append( Playlist( uri = doc[ "uri" ], name = doc[ "name" ], tracks = doc[ "tracks" ] ) )

        return playlists

    @playlists.setter  # noqa
    def playlists(self, playlists):
        raise NotImplementedError

    def delete(self, uri):
        self.mongo.remove( { 'uri' : uri } )

    def lookup(self, uri):
        doc = self.mongo.find_one( { 'uri' : uri } );
        
        for i in range( len( doc[ "tracks" ] ) ):
            doc[ "tracks" ][ i ] = self.backend.library.lookup( doc[ "tracks" ][ i ][ "file" ] )
            doc[ "tracks" ][ i ] = doc[ "tracks" ][ i ][ 0 ]

        return Playlist( uri = doc[ "uri" ], name = doc[ "name" ], tracks = doc[ "tracks" ] )

    def refresh(self):
        listener.BackendListener.send('playlists_loaded')

    def save(self, playlist):
        assert playlist.uri, 'Cannot save playlist without URI'
        playlistdoc = { 'uri' : playlist.uri, 'name' : playlist.name, 'tracks' : [] }

        for t in playlist.tracks:
            playlistdoc.append( { 'file' : t.file } )

        self.mongo.save( { 'uri' : playlist.uri }, playlistdoc )
        return self.lookup( playlist.uri )