#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# 
from __future__ import unicode_literals

import logging
import requests
import time

from mopidy.models import Track, Album, Artist

class memoized(object):
    def __init__(self, ctl=8, ttl=3600):
        self.cache = {}
        self.ctl = ctl
        self.ttl = ttl
        self._call_count = 1
 
    def __call__(self, func):
        def _memoized(*args):
            self.func = func
            now = time.time()
            try:
                value, last_update = self.cache[args]
                age = now - last_update
                if self._call_count >= self.ctl or \
                        age > self.ttl:
                    self._call_count = 1
                    raise AttributeError
 
                self._call_count += 1
                return value
 
            except (KeyError, AttributeError):
                value = self.func(*args)
                self.cache[args] = (value, now)
                return value
 
            except TypeError:
                return self.func(*args)
        return _memoized

def _convert_json_data(data , endpoint):
    if not data:
        return

    # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
    # See https://github.com/mopidy/mopidy/issues/302 for details.

    track_kwargs = {}
    album_kwargs = {}
    artist_kwargs = {}
    albumartist_kwargs = {}

    if 'track' in data:
        track_kwargs[b'track_no'] = int(data['track'])

    if 'tracktotal' in data:
        album_kwargs[b'num_tracks'] = int(data['tracktotal'])

    if 'artist' in data:
        artist_kwargs[b'name'] = data['artist']
        albumartist_kwargs[b'name'] = data['artist']

    if 'albumartist' in data:
        albumartist_kwargs[b'name'] = data['albumartist']

    if 'album' in data:
        album_kwargs[b'name'] = data['album']

    if 'title' in data:
        track_kwargs[b'name'] = data['title']

    if 'date' in data:
        track_kwargs[b'date'] = data['date']

    if 'mb_trackid' in data:
        track_kwargs[b'musicbrainz_id'] = data['mb_trackid']

    if 'mb_albumid' in data:
        album_kwargs[b'musicbrainz_id'] = data['mb_albumid']

    if 'mb_artistid' in data:
        artist_kwargs[b'musicbrainz_id'] = data['mb_artistid']

    if 'mb_albumartistid' in data:
        albumartist_kwargs[b'musicbrainz_id'] = (
            data['mb_albumartistid'])


    if artist_kwargs:
        artist = Artist(**artist_kwargs)
        track_kwargs[b'artists'] = [artist]

    if albumartist_kwargs:
        albumartist = Artist(**albumartist_kwargs)
        album_kwargs[b'artists'] = [albumartist]

    if album_kwargs:
        album = Album(**album_kwargs)
        track_kwargs[b'album'] = album

    track_kwargs[b'uri'] = "%s/item/%s/file" % (endpoint, data['id'])
    track_kwargs[b'length'] = int(data.get('length', 0)) * 1000

    track = Track(**track_kwargs)

    return track

class BeetsRemoteClient(object):

  def __init__(self, endpoint):
    super(BeetsRemoteClient, self).__init__()
    self.api_endpoint = endpoint

  def get_tracks(self):
    self._get("/items/")
    pass

  def get_track(self, id):
    self._get("/items/%s" % id)
    pass

  @memoized()
  def get_albums(self):
    album_ids = self._get("/album/").get("album_ids")
    for album_id in album_ids:
      print(self.get_album(album_id).get("title"))
    return {}

  @memoized()
  def get_album(self, id):
    return self._get("/album/%s" % id)

  @memoized()
  def get_album_by(self, name):
    res = self._get("/album/query/%s" % name).get("results")
    if len(res)>0:
      tracks = []
      for jtrack in res[0]["items"]:
        tracks.append(_convert_json_data(jtrack, self.api_endpoint ))
      return tracks

  @memoized()
  def get_artists(self):
    ## albums then look into tracks tag
    self._get("/albums/")
    pass

  def _get(self, url):
    if self.api_endpoint:
      url = self.api_endpoint + url
      print("get url", url)
      req = requests.get(url)
      return req.json()