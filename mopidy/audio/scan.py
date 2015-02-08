from __future__ import absolute_import, division, unicode_literals

import time

import pygst
pygst.require('0.10')
import gst  # noqa

from mopidy import exceptions
from mopidy.audio import utils
from mopidy.utils import encoding


class Scanner(object):
    """
    Helper to get tags and other relevant info from URIs.

    :param timeout: timeout for scanning a URI in ms
    :type event: int
    """

    def __init__(self, timeout=1000):
        self._timeout_ms = timeout

        sink = gst.element_factory_make('fakesink')

        audio_caps = gst.Caps(b'audio/x-raw-int; audio/x-raw-float')

        def pad_added(src, pad):
            return pad.link(sink.get_pad('sink'))

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
        :return: (tags, duration) pair. tags is a dictionary of lists for all
            the tags we found and duration is the length of the URI in
            milliseconds, or :class:`None` if the URI has no duration.
        """
        tags, duration = None, None
        try:
            self._setup(uri)
            tags = self._collect()
            duration = self._query_duration()
        finally:
            self._reset()

        return tags, duration

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
        timeout_s = self._timeout_ms / 1000.0
        tags = {}

        while time.time() - start < timeout_s:
            if not self._bus.have_pending():
                continue
            message = self._bus.pop()

            if message.type == gst.MESSAGE_ERROR:
                raise exceptions.ScannerError(
                    encoding.locale_decode(message.parse_error()[0]))
            elif message.type == gst.MESSAGE_EOS:
                return tags
            elif message.type == gst.MESSAGE_ASYNC_DONE:
                if message.src == self._pipe:
                    return tags
            elif message.type == gst.MESSAGE_TAG:
                taglist = message.parse_tag()
                # Note that this will only keep the last tag.
                tags.update(utils.convert_taglist(taglist))

        raise exceptions.ScannerError('Timeout after %dms' % self._timeout_ms)

    def _reset(self):
        """Ensures we cleanup child elements and flush the bus."""
        self._bus.set_flushing(True)
        self._pipe.set_state(gst.STATE_NULL)

    def _query_duration(self):
        try:
            duration = self._pipe.query_duration(gst.FORMAT_TIME, None)[0]
        except gst.QueryError:
            return None

        if duration < 0:
            return None
        else:
            return duration // gst.MSECOND
