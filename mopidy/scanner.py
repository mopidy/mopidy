import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst

from os.path import abspath
import datetime
import sys
import threading

from mopidy.utils.path import path_to_uri, find_files
from mopidy.models import Track, Artist, Album

def translator(data):
    album = Album(
        name=data['album'],
        num_tracks=data['track-count'],
    )

    artist = Artist(
        name=data['artist'],
    )

    date = datetime.date(
        data['date'].year,
        data['date'].month,
        data['date'].day,
    )

    return Track(
        uri=data['uri'],
        name=data['title'],
        album=album,
        artists=[artist],
        date=date,
        track_no=data['track-number'],
        length=data['duration'],
    )


class Scanner(object):
    def __init__(self, folder, data_callback, error_callback=None):
        self.uris = [path_to_uri(f) for f in find_files(folder)]
        self.data_callback = data_callback
        self.error_callback = error_callback
        self.loop = gobject.MainLoop()

        fakesink = gst.element_factory_make('fakesink')
        pad = fakesink.get_pad('sink')

        self.uribin = gst.element_factory_make('uridecodebin')
        self.uribin.connect('pad-added', self.process_new_pad, pad)

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
        data['uri'] = self.uribin.get_property('uri')
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
        self.next_uri()
        self.loop.run()

    def stop(self):
        self.loop.quit()
