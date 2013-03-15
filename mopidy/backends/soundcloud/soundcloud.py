#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import requests
import time

from mopidy.models import Track, Artist, Album

logger = logging.getLogger('mopidy.backends.soundcloud.client')


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
                if (self._call_count >= self.ctrl
                        or age > self.ttl):
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


class SoundcloudClient(object):

    CLIENT_ID = '93e33e327fd8a9b77becd179652272e2'
    CLIENT_SECRET = 'f1a2e1ff740f3e1e340e6993ceb18583'
    BRAND = u'☁'

    def __init__(self, username):
        super(SoundcloudClient, self).__init__()
        self.user_id = self.get_user_id(username)

    def get_user_id(self, username):
        try:
            user = self._get(
                'resolve.json?url=http://soundcloud.com/%s' % username)
            logger.info('User id for username %s is %s' % (
                username, user.get('id')))
            return user.get('id')
        except Exception:
            raise logger.error('No id for %s, status code %s' % (
                username, user.status_code))

    def get_favorites(self):
        favorites = self._get('users/%s/favorites.json' % self.user_id)
        return self.parse_results(favorites, True)

    @cache(ctl=100)
    def get_track(self, id, streamable=False):
        return self.parse_track(self._get('tracks/%s.json' % id), streamable)

    @cache()
    def get_user_stream(self):
        # User timeline like playlist which uses undocumented api
        # https://api.soundcloud.com/e1/users/USER_ID/stream.json?offset=0
        # returns five elements per request
        tracks = []
        for sid in xrange(0, 4):
            stream = self._get('e1/users/%s/stream.json?offset=%s' % (
                self.user_id, sid * 5))
            for data in stream:
                if data.get('track'):
                    tracks.append(self.parse_track(data.get('track'), True))
                if data.get('playlist'):
                    ttracks.extend(self.parse_results(data.get('playlist').get('tracks'), True))
        return self.sanitize_tracks(tracks)

    @cache()
    def get_sets(self):
        playlists = self._get('users/%s/playlists.json' % self.user_id)
        tplaylists = []
        for playlist in playlists:

            name = '%s on SoundCloud' % playlist.get('title')
            uri = playlist.get('permalink')
            tracks = self.parse_results(playlist.get('tracks'), True)
            logger.info('Fetched set %s with id %s' % (name, uri))
            logger.debug(tracks)
            tplaylists.append((name, uri, tracks))
        return tplaylists
    
    @cache()
    def search(self, query):
        'SoundCloud API only supports basic query no artist,'
        'album queries are possible'
        # TODO: add genre filter
        res = self._get(
            'tracks.json?q=%s&filter=streamable&order=hotness' % query)
        tracks = []
        for track in res:
            tracks.append(self.parse_track(track, False, True))
        return self.sanitize_tracks(tracks)

    def parse_results(self, res, streamable=False):
        tracks = []
        for track in res:
            tracks.append(self.parse_track(track, streamable))
        return self.sanitize_tracks(tracks)

    def _get(self, url):

        # TODO: Optimize
        if '?' in url:
            url = '%s&client_id=%s' % (url, self.CLIENT_ID)
        else:
            url = '%s?client_id=%s' % (url, self.CLIENT_ID)

        url = 'https://api.soundcloud.com/%s' % url

        logger.debug('Requesting %s' % url)
        req = requests.get(url)
        if req.status_code != 200:
            raise logger.error('Request %s, failed with status code %s' % (
                url, req.status_code))
        try:
            return req.json()
        except Exception as e:
            raise logger.error('Request %s, failed with error %s' % (
                url, e))

    def sanitize_tracks(self, tracks):
        return filter(None, tracks)

    def parse_track(self, data, remote_url=False, is_search=False):
        if not data:
            return
        if not data['streamable']:
            return
        if not data['kind'] == 'track':
            return

        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details.

        track_kwargs = {}
        artist_kwargs = {}
        album_kwargs = {}

        if 'title' in data:
            name = data['title']

            # NOTE On some clients search UI would group results by artist
            # thus prevent user from selecting track
            if not is_search:
                if ' - ' in name:
                    name = name.split(' - ')
                    track_kwargs[b'name'] = name[1]
                    artist_kwargs[b'name'] = name[0]
                elif 'label_name' in data and data['label_name'] != '':
                    track_kwargs[b'name'] = name
                    artist_kwargs[b'name'] = data['label_name']
                else:
                    track_kwargs[b'name'] = name
                    artist_kwargs[b'name'] = data.get('user').get('username')

                album_kwargs[b'name'] = 'SoundCloud'
            else:
                ## NOTE mpdroid removes ☁ from track name, probably others too
                track_kwargs[b'name'] = '%s %s' % (self.BRAND, name)

        if 'date' in data:
            track_kwargs[b'date'] = data['date']

        if remote_url:
            track_kwargs[b'uri'] = '%s?client_id=%s' % (
                data['stream_url'], self.CLIENT_ID)
        else:
            track_kwargs[b'uri'] = 'soundcloud://%s' % data['id']

        track_kwargs[b'length'] = int(data.get('duration', 0))

        if artist_kwargs:
            artist = Artist(**artist_kwargs)
            track_kwargs[b'artists'] = [artist]

        if 'artwork_url' in data:
            album_kwargs[b'images'] = [data['artwork_url']]

        if album_kwargs:
            album = Album(**album_kwargs)
            track_kwargs[b'album'] = album

        track = Track(**track_kwargs)
        return track
