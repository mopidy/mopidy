import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst

import datetime

from mopidy.utils.path import path_to_uri, find_files
from mopidy.models import Track, Artist, Album

def translator(data):
    albumartist_kwargs = {}
    album_kwargs = {}
    artist_kwargs = {}
    track_kwargs = {}

    # FIXME replace with data.get('foo', None) ?

    if 'album' in data:
        album_kwargs['name'] = data['album']

    if 'track-count' in data:
        album_kwargs['num_tracks'] = data['track-count']

    if 'artist' in data:
        artist_kwargs['name'] = data['artist']

    if 'date' in data:
        date = data['date']
        date = datetime.date(date.year, date.month, date.day)
        track_kwargs['date'] = date

    if 'title' in data:
        track_kwargs['name'] = data['title']

    if 'track-number' in data:
        track_kwargs['track_no'] = data['track-number']

    if 'album-artist' in data:
        albumartist_kwargs['name'] = data['album-artist']

    if 'musicbrainz-trackid' in data:
        track_kwargs['musicbrainz_id'] = data['musicbrainz-trackid']

    if 'musicbrainz-artistid' in data:
        artist_kwargs['musicbrainz_id'] = data['musicbrainz-artistid']

    if 'musicbrainz-albumid' in data:
        album_kwargs['musicbrainz_id'] = data['musicbrainz-albumid']

    if 'musicbrainz-albumartistid' in data:
        albumartist_kwargs['musicbrainz_id'] = data['musicbrainz-albumartistid']

    if albumartist_kwargs:
        album_kwargs['artists'] = [Artist(**albumartist_kwargs)]

    track_kwargs['uri'] = data['uri']
    track_kwargs['length'] = data['duration']
    track_kwargs['album'] = Album(**album_kwargs)
    track_kwargs['artists'] = [Artist(**artist_kwargs)]

    return Track(**track_kwargs)


class Scanner(object):
    def __init__(self, folder, data_callback, error_callback=None):
        self.uris = [path_to_uri(f) for f in find_files(folder)]
        self.data_callback = data_callback
        self.error_callback = error_callback
        self.loop = gobject.MainLoop()

        caps = gst.Caps('audio/x-raw-int')
        fakesink = gst.element_factory_make('fakesink')
        pad = fakesink.get_pad('sink')

        self.uribin = gst.element_factory_make('uridecodebin')
        self.uribin.connect('pad-added', self.process_new_pad, pad)
        self.uribin.set_property('caps', caps)

        self.pipe = gst.element_factory_make('pipeline')
        self.pipe.add(fakesink)
        self.pipe.add(self.uribin)

        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect('message::tag', self.process_tags)
        bus.connect('message::error', self.process_error)

    def process_new_pad(self, source, pad, target_pad):
        pad.link(target_pad)

    def process_tags(self, bus, message):
        data = message.parse_tag()
        data = dict([(k, data[k]) for k in data.keys()])
        data['uri'] = unicode(self.uribin.get_property('uri'))
        data['duration'] = self.get_duration()
        self.data_callback(data)
        self.next_uri()

    def process_error(self, bus, message):
        if self.error_callback:
            uri = self.uribin.get_property('uri')
            errors = message.parse_error()
            self.error_callback(uri, errors)
        self.next_uri()

    def get_duration(self):
        self.pipe.get_state()
        try:
            return self.pipe.query_duration(
                gst.FORMAT_TIME, None)[0] // gst.MSECOND
        except gst.QueryError:
            return None

    def next_uri(self):
        if not self.uris:
            return self.stop()

        self.pipe.set_state(gst.STATE_NULL)
        self.uribin.set_property('uri', self.uris.pop())
        self.pipe.set_state(gst.STATE_PAUSED)

    def start(self):
        if not self.uris:
            return
        self.next_uri()
        self.loop.run()

    def stop(self):
        self.pipe.set_state(gst.STATE_NULL)
        self.loop.quit()
