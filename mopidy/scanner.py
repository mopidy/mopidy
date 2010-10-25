import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst

from os.path import abspath
import sys
import threading

from mopidy.utils.path import path_to_uri

class Scanner(object):
    def __init__(self, files, callback):
        self.uris = [path_to_uri(abspath(f)) for f in files]
        self.callback = callback
        self.loop = gobject.MainLoop()

        self.pipe = gst.element_factory_make('playbin2')

        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect('message::tag', self.process_message)

        self.next_uri()

    def process_message(self, bus, message):
        data = message.parse_tag()
        self.callback(dict([(k, data[k]) for k in data.keys()]))
        self.next_uri()

    def next_uri(self):
        if not self.uris:
            return self.stop()

        self.pipe.set_state(gst.STATE_NULL)
        self.pipe.set_property('uri', self.uris.pop())
        self.pipe.set_state(gst.STATE_PAUSED)

    def start(self):
        self.loop.run()

    def stop(self):
        self.loop.quit()
