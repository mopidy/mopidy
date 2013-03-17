#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import logging
import requests
import time

from requests.exceptions import RequestException
from mopidy.models import Track, Album, Artist

logger = logging.getLogger('mopidy.backends.beets.client')


class cache(object):
    ## TODO: merge this to util library
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


class BeetsRemoteClient(object):

    def __init__(self, endpoint):
        super(BeetsRemoteClient, self).__init__()
        self.api = requests.Session()
        if endpoint:
            self.api_endpoint = endpoint
            logger.info('Connecting to Beets remote library %s', endpoint)
            try:
                self._get('/')
            except Exception as e:
                logger.error('SoundCloud Authentication error: %s' % e)
        else:
            logger.error('Beets API url is not defined')

    @cache()
    def get_tracks(self):
        track_ids = self._get('/item/').get('item_ids')
        tracks = []
        for track_id in track_ids:
            tracks.append(self.get_track(track_id))
        return tracks

    @cache(ctl=16)
    def get_track(self, id, remote_url=False):
        return self._convert_json_data(self._get('/item/%s' % id), remote_url)

    @cache()
    def get_item_by(self, name):
        res = self._get('/item/query/%s' % name).get('results')
        return self._parse_query(res)

    @cache()
    def get_album_by(self, name):
        res = self._get('/album/query/%s' % name).get('results')
        return self._parse_query(res[0]['items'])

    def _get(self, url):
        try:
            url = self.api_endpoint + url
            logger.debug('Requesting %s' % url)
            req = self.api.get(url)
            if req.status_code != 200:
                raise logger.error('Request %s, failed with status code %s' % (
                    url, req.status_code))

            return req.json()
        except Exception as e:
            logger.error('Request %s, failed with error %s' % (
                url, e))

    def _parse_query(self, res):
        if len(res) > 0:
            tracks = []
            for track in res:
                tracks.append(self._convert_json_data(track))
            return tracks
        return None

    def _convert_json_data(self, data, remote_url=False):
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

        if 'album_id' in data:
            album_art_url = '%s/album/%s/art' % (
                self.api_endpoint, data['album_id'])
            album_kwargs[b'images'] = [album_art_url]

        if artist_kwargs:
            artist = Artist(**artist_kwargs)
            track_kwargs[b'artists'] = [artist]

        if albumartist_kwargs:
            albumartist = Artist(**albumartist_kwargs)
            album_kwargs[b'artists'] = [albumartist]

        if album_kwargs:
            album = Album(**album_kwargs)
            track_kwargs[b'album'] = album

        if remote_url:
            track_kwargs[b'uri'] = '%s/item/%s/file' % (
                self.api_endpoint, data['id'])
        else:
            track_kwargs[b'uri'] = 'beets://%s' % data['id']
        track_kwargs[b'length'] = int(data.get('length', 0)) * 1000

        track = Track(**track_kwargs)

        return track
