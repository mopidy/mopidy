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
            data = {'uri': uri}
            self._setup(uri)
            data['tags'] = self._collect()
            data['mtime'] = self._query_mtime(uri)
            data['duration'] = self._query_duration()
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
                # Taglists are not really dicts, hence the key usage.
                # Beyond that, we only keep the last tag for each key,
                # as we assume this is the best, and force everything
                # to lists.
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


def audio_data_to_track(data):
    """Convert taglist data + our extras to a track."""
    tags = data['tags']
    album_kwargs = {}
    track_kwargs = {}

    def _retrieve(source_key, target_key, target, convert):
        if tags.get(source_key, None):
            result = convert(tags[source_key])
            target.setdefault(target_key, result)

    first = lambda values: values[0]
    join = lambda values: ', '.join(values)
    artists = lambda values: [Artist(name=v) for v in values]

    _retrieve(gst.TAG_ARTIST, 'artists', track_kwargs, artists)
    _retrieve(gst.TAG_COMPOSER, 'composers', track_kwargs, artists)
    _retrieve(gst.TAG_PERFORMER, 'performers', track_kwargs, artists)
    _retrieve(gst.TAG_TITLE, 'name', track_kwargs, join)
    _retrieve(gst.TAG_TRACK_NUMBER, 'track_no', track_kwargs, first)
    _retrieve(gst.TAG_ALBUM_VOLUME_NUMBER, 'disc_no', track_kwargs, first)
    _retrieve(gst.TAG_GENRE, 'genre', track_kwargs, join)
    _retrieve(gst.TAG_BITRATE, 'bitrate', track_kwargs, first)

    _retrieve(gst.TAG_ALBUM, 'name', album_kwargs, join)
    _retrieve(gst.TAG_ALBUM_ARTIST, 'artists', album_kwargs, artists)
    _retrieve(gst.TAG_TRACK_COUNT, 'num_tracks', album_kwargs, first)
    _retrieve(gst.TAG_ALBUM_VOLUME_COUNT, 'num_discs', album_kwargs, first)

    # Following keys don't seem to have TAG_* constant.
    _retrieve('comment', 'comment', track_kwargs, join)
    _retrieve('musicbrainz-trackid', 'musicbrainz_id', track_kwargs, first)
    _retrieve('musicbrainz-albumid', 'musicbrainz_id', album_kwargs, first)

    # For streams, will not override if a better value has already been set.
    _retrieve(gst.TAG_ORGANIZATION, 'name', track_kwargs, join)
    _retrieve(gst.TAG_LOCATION, 'comment', track_kwargs, join)
    _retrieve(gst.TAG_COPYRIGHT, 'comment', track_kwargs, join)

    if tags.get(gst.TAG_DATE, None):
        date = tags[gst.TAG_DATE][0]
        try:
            date = datetime.date(date.year, date.month, date.day)
        except ValueError:
            pass  # Ignore invalid dates
        else:
            track_kwargs['date'] = date.isoformat()

    def _retrive_mb_artistid(source_key, target):
        if source_key in tags and len(target.get('artists', [])) == 1:
            target['artists'][0] = target['artists'][0].copy(
                musicbrainz_id=tags[source_key][0])

    _retrive_mb_artistid('musicbrainz-artistid', track_kwargs)
    _retrive_mb_artistid('musicbrainz-albumartistid', album_kwargs)

    if data['mtime']:
        track_kwargs['last_modified'] = int(data['mtime'])

    if data[gst.TAG_DURATION]:
        track_kwargs['length'] = data[gst.TAG_DURATION] // gst.MSECOND

    track_kwargs['uri'] = data['uri']
    track_kwargs['album'] = Album(**album_kwargs)
    return Track(**track_kwargs)
