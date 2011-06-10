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

    def _retrieve(source_key, target_key, target):
        if source_key in data:
            target[target_key] = data[source_key]

    _retrieve(gst.TAG_ALBUM, 'name', album_kwargs)
    _retrieve(gst.TAG_TRACK_COUNT, 'num_tracks', album_kwargs)
    _retrieve(gst.TAG_ARTIST, 'name', artist_kwargs)

    if gst.TAG_DATE in data and data[gst.TAG_DATE]:
        date = data[gst.TAG_DATE]
        date = datetime.date(date.year, date.month, date.day)
        track_kwargs['date'] = date

    _retrieve(gst.TAG_TITLE, 'name', track_kwargs)
    _retrieve(gst.TAG_TRACK_NUMBER, 'track_no', track_kwargs)

    # Following keys don't seem to have TAG_* constant.
    _retrieve('album-artist', 'name', albumartist_kwargs)
    _retrieve('musicbrainz-trackid', 'musicbrainz_id', track_kwargs)
    _retrieve('musicbrainz-artistid', 'musicbrainz_id', artist_kwargs)
    _retrieve('musicbrainz-albumid', 'musicbrainz_id', album_kwargs)
    _retrieve('musicbrainz-albumartistid', 'musicbrainz_id', albumartist_kwargs)

    if albumartist_kwargs:
        album_kwargs['artists'] = [Artist(**albumartist_kwargs)]

    track_kwargs['uri'] = data['uri']
    track_kwargs['length'] = data[gst.TAG_DURATION]
    track_kwargs['album'] = Album(**album_kwargs)
    track_kwargs['artists'] = [Artist(**artist_kwargs)]

    return Track(**track_kwargs)


class Scanner(object):
    def __init__(self, folder, data_callback, error_callback=None):
        self.uris = [path_to_uri(f) for f in find_files(folder)]
        self.data_callback = data_callback
        self.error_callback = error_callback
        self.loop = gobject.MainLoop()

        fakesink = gst.element_factory_make('fakesink')

        self.uribin = gst.element_factory_make('uridecodebin')
        self.uribin.set_property('caps', gst.Caps('audio/x-raw-int'))
        self.uribin.connect('pad-added', self.process_new_pad,
            fakesink.get_pad('sink'))

        self.pipe = gst.element_factory_make('pipeline')
        self.pipe.add(self.uribin)
        self.pipe.add(fakesink)

        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect('message::tag', self.process_tags)
        bus.connect('message::error', self.process_error)

    def process_new_pad(self, source, pad, target_pad):
        pad.link(target_pad)

    def process_tags(self, bus, message):
        taglist = message.parse_tag()
        data = {
            'uri': unicode(self.uribin.get_property('uri')),
            gst.TAG_DURATION: self.get_duration(),
        }

        for key in taglist.keys():
            # XXX: For some crazy reason some wma files spit out lists here,
            # not sure if this is due to better data in headers or wma being
            # stupid. So ugly hack for now :/
            if type(taglist[key]) is list:
                data[key] = taglist[key][0]
            else:
                data[key] = taglist[key]

        try:
            self.data_callback(data)
            self.next_uri()
        except KeyboardInterrupt:
            self.stop()

    def process_error(self, bus, message):
        if self.error_callback:
            uri = self.uribin.get_property('uri')
            error, debug = message.parse_error()
            self.error_callback(uri, error, debug)
        self.next_uri()

    def get_duration(self):
        self.pipe.get_state() # Block until state change is done.
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
