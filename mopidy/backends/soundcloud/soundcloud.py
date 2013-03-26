#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import requests
import time

from requests.exceptions import RequestException
from mopidy.models import Track, Artist, Album
from urllib import quote_plus

logger = logging.getLogger('mopidy.backends.soundcloud.client')


class cache(object):
    # TODO: merge this to util library

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


class SoundCloudClient(object):

    CLIENT_ID = '93e33e327fd8a9b77becd179652272e2'

    def __init__(self, token):
        super(SoundCloudClient, self).__init__()
        self.SC = requests.Session()
        self.SC.headers.update({'Authorization': 'OAuth %s' % token})
        self.user = self.get_user()
        logger.info('User id for username %s is %s' % (
            self.user.get('username'), self.user.get('id')))

    @cache()
    def get_user(self):
        try:
            return self._get('me.json')
        except Exception as e:
            logger.error('SoundCloud Authentication error: %s' % e)

    # Private

    @cache()
    def get_user_stream(self):
        # User timeline like playlist which uses undocumented api
        # https://api.soundcloud.com/e1/me/stream.json?offset=0
        # returns five elements per request
        tracks = []
        for sid in xrange(0, 2):
            stream = self._get('e1/me/stream.json?offset=%s' % sid * 5)
            for data in stream.get('collection'):
                try:
                    kind = data.get('type')
                    # multiple types of track with same data
                    if 'track' in kind:
                        tracks.append(self.parse_track(data.get('track')))
                    if kind == 'playlist':
                        tracks.extend(self.parse_results(
                            data.get('playlist').get('tracks')))
                except Exception:
                    # Type not supported or SC changed API
                    pass

        return self.sanitize_tracks(tracks)

    @cache()
    def get_sets(self):
        playlists = self._get('users/%s/playlists.json' % self.user.get('id'))
        tplaylists = []
        for playlist in playlists:
            name = '%s on SoundCloud' % playlist.get('title')
            uri = playlist.get('permalink')
            tracks = self.parse_results(playlist.get('tracks'))
            logger.info('Fetched set %s with id %s' % (name, uri))
            tplaylists.append((name, uri, tracks))
        return tplaylists

    def get_user_favorites(self):
        favorites = self._get('users/%s/favorites.json' % self.user.get('id'))
        return self.parse_results(favorites)

    # Public

    @cache(ctl=100)
    def get_track(self, id, streamable=False):
        try:
            # TODO better way to handle deleted tracks
            return self.parse_track(self._get('tracks/%s.json' % id), streamable)
        except Exception:
            return

    @cache()
    def get_explore_category(self, category, section):
        logger.info("get_explore_category %s %s" % (category, section))
        # Most liked by category in explore section
        tracks = []
        for sid in xrange(0, 2):
            stream = self._get('explore/sounds/category/%s?offset=%s' % (
                category.lower(), sid * 20))
            for data in stream.get('collection'):
                if data.get('name') == section:
                    for track in data.get('tracks'):
                        tracks.append(self.get_track(track.get('id')))
        return self.sanitize_tracks(tracks)

    @cache()
    def search(self, query):
        'SoundCloud API only supports basic query no artist,'
        'album queries are possible'
        # TODO: add genre filter
        res = self._get(
            'tracks.json?q=%s&filter=streamable&order=hotness' %
            quote_plus(query))

        tracks = []
        for track in res:
            tracks.append(self.parse_track(track, False, True))
        return self.sanitize_tracks(tracks)

    def parse_results(self, res):
        tracks = []
        for track in res:
            tracks.append(self.parse_track(track))
        return self.sanitize_tracks(tracks)

    def _get(self, url):

        # TODO: Optimize
        if '?' in url:
            url = '%s&client_id=%s' % (url, self.CLIENT_ID)
        else:
            url = '%s?client_id=%s' % (url, self.CLIENT_ID)

        url = 'https://api.soundcloud.com/%s' % url

        logger.debug('Requesting %s' % url)
        req = self.SC.get(url)
        if req.status_code != 200:
            raise logger.error('Request %s, failed with status code %s' % (
                url, req.status_code))
        try:
            return req.json()
        except RequestException as e:
            logger.error('Request %s, failed with error %s' % (
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
        if not self.can_be_streamed(data['stream_url']):
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

        if 'date' in data:
            track_kwargs[b'date'] = data['date']

        if remote_url:
            track_kwargs[b'uri'] = self.get_streamble_url(data['stream_url'])
        else:
            track_kwargs[b'uri'] = 'soundcloud:song;%s' % data['id']

        track_kwargs[b'length'] = int(data.get('duration', 0))

        if artist_kwargs:
            artist = Artist(**artist_kwargs)
            track_kwargs[b'artists'] = [artist]

        if album_kwargs:
            if 'artwork_url' in data and data['artwork_url']:
                album_kwargs[b'images'] = [data['artwork_url']]
            else:
                image = data.get('user').get('avatar_url')
                if image:
                    album_kwargs[b'images'] = [image]
                else:
                    album_kwargs[b'images'] = []

            album = Album(**album_kwargs)
            track_kwargs[b'album'] = album

        track = Track(**track_kwargs)
        return track

    def can_be_streamed(self, url):
        req = self.SC.head(self.get_streamble_url(url))
        return req.status_code == 302

    def get_streamble_url(self, url):
        return '%s?client_id=%s' % (url, self.CLIENT_ID)
