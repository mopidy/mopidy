#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import logging
import requests
import time

from mopidy.models import Track, Artist

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


class SoundcloudClient(object):

    CLIENT_ID = "93e33e327fd8a9b77becd179652272e2"
    CLIENT_SECRET = "f1a2e1ff740f3e1e340e6993ceb18583"

    def __init__(self, username):
        super(SoundcloudClient, self).__init__()
        self.user_id = self.get_userid(username)

    def get_userid(self, username):
        try:
            user = self._get("resolve.json?url=http://soundcloud.com/%s" % username)
            return user.get("id")
        except Exception:
            raise logger.error('Can\'t get id for %s, status code %s' % (
                username, user.status_code))

    @cache()
    def get_favorites(self):
        favorites = self._get("users/%s/favorites.json" % self.user_id)
        return self.parse_results(favorites, True)

    @cache(ctl=100)
    def get_track(self, id, streamable=False):
        return self.parse_track(self._get('tracks/%s.json' % id), streamable)

    @cache()
    def search(self, query):

        res = self._get('tracks.json?q=%s&filter=all&order=hotness' % query)
        tracks = []
        for track in res:
            tracks.append(self.parse_track(track, False, True))
        return tracks

    def parse_results(self, res, streamable=False):
        tracks = []
        for track in res:
            tracks.append(self.parse_track(track, streamable))
        return tracks

    def _get(self, url):

        if '?' in url:
            url = "%s&client_id=%s" % (url, self.CLIENT_ID)
        else:
            url = "%s?client_id=%s" % (url, self.CLIENT_ID)

        url = 'https://api.soundcloud.com/%s' % url

        logger.debug('Requesting %s' % url)
        req = requests.get(url)
        if req.status_code != 200:
            raise logger.error('Request %s, failed with status code %s' % (
                url, req.status_code))
        try:
            return req.json()
        except Exception:
            return req

    def parse_track(self, data, remote_url=False, is_search=False):
        if not data:
            return
        if not data["kind"] == "track":
            return
        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details.

        track_kwargs = {}
        artist_kwargs = {}

        if 'title' in data:
            name = data['title']
            if " - " in name and not is_search:
                name = name.split(" - ")
                track_kwargs[b'name'] = name[1]
                artist_kwargs[b'name'] = name[0]
            else:
                track_kwargs[b'name'] = name

        if 'date' in data:
            track_kwargs[b'date'] = data['date']

        if remote_url:
            track_kwargs[b'uri'] = "%s?client_id=%s" % (
                data['stream_url'], self.CLIENT_ID)
        else:
            track_kwargs[b'uri'] = 'soundcloud://%s' % data['id']

        track_kwargs[b'length'] = int(data.get('duration', 0))

        if artist_kwargs:
            artist = Artist(**artist_kwargs)
            track_kwargs[b'artists'] = [artist]

        track = Track(**track_kwargs)

        return track
