from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst
import gobject

import time

from mopidy import exceptions


class Scanner(object):
    def __init__(self, timeout=1000):
        self.timeout_ms = timeout

        sink = gst.element_factory_make('fakesink')

        audio_caps = gst.Caps(b'audio/x-raw-int; audio/x-raw-float')
        pad_added = lambda src, pad: pad.link(sink.get_pad('sink'))

        self.uribin = gst.element_factory_make('uridecodebin')
        self.uribin.set_property('caps', audio_caps)
        self.uribin.connect('pad-added', pad_added)

        self.pipe = gst.element_factory_make('pipeline')
        self.pipe.add(self.uribin)
        self.pipe.add(sink)

        self.bus = self.pipe.get_bus()
        self.bus.set_flushing(True)

    def scan(self, uri):
        try:
            self._setup(uri)
            data = self._collect()
            # Make sure uri and duration does not come from tags.
            data[b'uri'] = uri
            data[gst.TAG_DURATION] = self._query_duration()
        finally:
            self._reset()

        return data

    def _setup(self, uri):
        """Primes the pipeline for collection."""
        self.pipe.set_state(gst.STATE_READY)
        self.uribin.set_property(b'uri', uri)
        self.bus.set_flushing(False)
        self.pipe.set_state(gst.STATE_PAUSED)

    def _collect(self):
        """Polls for messages to collect data."""
        start = time.time()
        timeout_s = self.timeout_ms / float(1000)
        poll_timeout_ns = 1000
        data = {}

        while time.time() - start < timeout_s:
            message = self.bus.poll(gst.MESSAGE_ANY, poll_timeout_ns)

            if message is None:
                pass  # polling the bus timed out.
            elif message.type == gst.MESSAGE_ERROR:
                raise exceptions.ScannerError(message.parse_error()[0])
            elif message.type == gst.MESSAGE_EOS:
                return data
            elif message.type == gst.MESSAGE_ASYNC_DONE:
                if message.src == self.pipe:
                    return data
            elif message.type == gst.MESSAGE_TAG:
                taglist = message.parse_tag()
                for key in taglist.keys():
                    data[key] = taglist[key]

        raise exceptions.ScannerError('Timeout after %dms' % self.timeout_ms)

    def _reset(self):
        """Ensures we cleanup child elements and flush the bus."""
        self.bus.set_flushing(True)
        self.pipe.set_state(gst.STATE_NULL)

    def _query_duration(self):
        try:
            duration = self.pipe.query_duration(gst.FORMAT_TIME, None)[0]
            return duration // gst.MSECOND
        except gst.QueryError:
            return None
