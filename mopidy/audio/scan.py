from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst

import datetime
import os
import time

from mopidy import exceptions
from mopidy.models import Track, Artist, Album
from mopidy.utils import path


class Scanner(object):
    """
    Helper to get tags and other relevant info from URIs.

    :param timeout: timeout for scanning a URI in ms
    :type event: int
    :param min_duration: minimum duration of scanned URI in ms, -1 for all.
    :type event: int
    """

    def __init__(self, timeout=1000, min_duration=100):
        self._timeout_ms = timeout
        self._min_duration_ms = min_duration

        sink = gst.element_factory_make('fakesink')

        audio_caps = gst.Caps(b'audio/x-raw-int; audio/x-raw-float')
        pad_added = lambda src, pad: pad.link(sink.get_pad('sink'))

        self._uribin = gst.element_factory_make('uridecodebin')
        self._uribin.set_property('caps', audio_caps)
        self._uribin.connect('pad-added', pad_added)

        self._pipe = gst.element_factory_make('pipeline')
        self._pipe.add(self._uribin)
        self._pipe.add(sink)

        self._bus = self._pipe.get_bus()
        self._bus.set_flushing(True)

    def scan(self, uri):
        """
        Scan the given uri collecting relevant metadata.

        :param uri: URI of the resource to scan.
        :type event: string
        :return: Dictionary of tags, duration, mtime and uri information.
        """
        try:
            self._setup(uri)
            tags = self._collect()  # Ensure collect before queries.
            data = {'uri': uri, 'tags': tags,
                    'mtime': self._query_mtime(uri),
                    'duration': self._query_duration()}
        finally:
            self._reset()

        if self._min_duration_ms is None:
            return data
        elif data['duration'] >= self._min_duration_ms * gst.MSECOND:
            return data

        raise exceptions.ScannerError('Rejecting file with less than %dms '
                                      'audio data.' % self._min_duration_ms)

    def _setup(self, uri):
        """Primes the pipeline for collection."""
        self._pipe.set_state(gst.STATE_READY)
        self._uribin.set_property(b'uri', uri)
        self._bus.set_flushing(False)
        result = self._pipe.set_state(gst.STATE_PAUSED)
        if result == gst.STATE_CHANGE_NO_PREROLL:
            # Live sources don't pre-roll, so set to playing to get data.
            self._pipe.set_state(gst.STATE_PLAYING)

    def _collect(self):
        """Polls for messages to collect data."""
        start = time.time()
        timeout_s = self._timeout_ms / float(1000)
        tags = {}

        while time.time() - start < timeout_s:
            if not self._bus.have_pending():
                continue
            message = self._bus.pop()

            if message.type == gst.MESSAGE_ERROR:
                raise exceptions.ScannerError(message.parse_error()[0])
            elif message.type == gst.MESSAGE_EOS:
                return tags
            elif message.type == gst.MESSAGE_ASYNC_DONE:
                if message.src == self._pipe:
                    return tags
            elif message.type == gst.MESSAGE_TAG:
                # Taglists are not really dicts, hence the lack of .items() and
                # explicit .keys. We only keep the last tag for each key, as we
                # assume this is the best, some formats will produce multiple
                # taglists. Lastly we force everything to lists for conformity.
                taglist = message.parse_tag()
                for key in taglist.keys():
                    value = taglist[key]
                    if not isinstance(value, list):
                        value = [value]
                    tags[key] = value

        raise exceptions.ScannerError('Timeout after %dms' % self._timeout_ms)

    def _reset(self):
        """Ensures we cleanup child elements and flush the bus."""
        self._bus.set_flushing(True)
        self._pipe.set_state(gst.STATE_NULL)

    def _query_duration(self):
        try:
            return self._pipe.query_duration(gst.FORMAT_TIME, None)[0]
        except gst.QueryError:
            return None

    def _query_mtime(self, uri):
        if not uri.startswith('file:'):
            return None
        return os.path.getmtime(path.uri_to_path(uri))


def _artists(tags, artist_name, artist_id=None):
    # Name missing, don't set artist
    if not tags.get(artist_name):
        return None
    # One artist name and id, provide artist with id.
    if len(tags[artist_name]) == 1 and artist_id in tags:
        return [Artist(name=tags[artist_name][0],
                       musicbrainz_id=tags[artist_id][0])]
    # Multiple artist, provide artists without id.
    return [Artist(name=name) for name in tags[artist_name]]


def _date(tags):
    if not tags.get(gst.TAG_DATE):
        return None
    try:
        date = tags[gst.TAG_DATE][0]
        return datetime.date(date.year, date.month, date.day).isoformat()
    except ValueError:
        return None


def audio_data_to_track(data):
    """Convert taglist data + our extras to a track."""
    tags = data['tags']
    album_kwargs = {}
    track_kwargs = {}

    track_kwargs['composers'] = _artists(tags, gst.TAG_COMPOSER)
    track_kwargs['performers'] = _artists(tags, gst.TAG_PERFORMER)
    track_kwargs['artists'] = _artists(
        tags, gst.TAG_ARTIST, 'musicbrainz-artistid')
    album_kwargs['artists'] = _artists(
        tags, gst.TAG_ALBUM_ARTIST, 'musicbrainz-albumartistid')

    track_kwargs['genre'] = '; '.join(tags.get(gst.TAG_GENRE, []))
    track_kwargs['name'] = '; '.join(tags.get(gst.TAG_TITLE, []))
    if not track_kwargs['name']:
        track_kwargs['name'] = '; '.join(tags.get(gst.TAG_ORGANIZATION, []))

    track_kwargs['comment'] = '; '.join(tags.get('comment', []))
    if not track_kwargs['comment']:
        track_kwargs['comment'] = '; '.join(tags.get(gst.TAG_LOCATION, []))
    if not track_kwargs['comment']:
        track_kwargs['comment'] = '; '.join(tags.get(gst.TAG_COPYRIGHT, []))

    track_kwargs['track_no'] = tags.get(gst.TAG_TRACK_NUMBER, [None])[0]
    track_kwargs['disc_no'] = tags.get(gst.TAG_ALBUM_VOLUME_NUMBER, [None])[0]
    track_kwargs['bitrate'] = tags.get(gst.TAG_BITRATE, [None])[0]
    track_kwargs['musicbrainz_id'] = tags.get('musicbrainz-trackid', [None])[0]

    album_kwargs['name'] = tags.get(gst.TAG_ALBUM, [None])[0]
    album_kwargs['num_tracks'] = tags.get(gst.TAG_TRACK_COUNT, [None])[0]
    album_kwargs['num_discs'] = tags.get(gst.TAG_ALBUM_VOLUME_COUNT, [None])[0]
    album_kwargs['musicbrainz_id'] = tags.get('musicbrainz-albumid', [None])[0]

    track_kwargs['date'] = _date(tags)
    track_kwargs['last_modified'] = int(data.get('mtime') or 0)
    track_kwargs['length'] = (data.get(gst.TAG_DURATION) or 0) // gst.MSECOND

    # Clear out any empty values we found
    track_kwargs = {k: v for k, v in track_kwargs.items() if v}
    album_kwargs = {k: v for k, v in album_kwargs.items() if v}

    track_kwargs['uri'] = data['uri']
    track_kwargs['album'] = Album(**album_kwargs)
    return Track(**track_kwargs)
