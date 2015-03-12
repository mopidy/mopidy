from __future__ import absolute_import, division, unicode_literals

import collections
import time

import pygst
pygst.require('0.10')
import gst  # noqa
import gst.pbutils

from mopidy import exceptions
from mopidy.audio import utils
from mopidy.utils import encoding

_missing_plugin_desc = gst.pbutils.missing_plugin_message_get_description

Result = collections.namedtuple(
    'Result', ('uri', 'tags', 'duration', 'seekable', 'mime'))


class Scanner(object):
    """
    Helper to get tags and other relevant info from URIs.

    :param timeout: timeout for scanning a URI in ms
    :param proxy_config: dictionary containing proxy config strings.
    :type event: int
    """

    def __init__(self, timeout=1000, proxy_config=None):
        self._timeout_ms = timeout
        self._proxy_config = proxy_config or {}

        sink = gst.element_factory_make('fakesink')
        self._src = None

        def pad_added(src, pad):
            return pad.link(sink.get_pad('sink'))

        def have_type(finder, probability, caps):
            msg = gst.message_new_application(finder, caps.get_structure(0))
            finder.get_bus().post(msg)

        self._typefinder = gst.element_factory_make('typefind')
        self._typefinder.connect('have-type', have_type)

        audio_caps = gst.Caps(b'audio/x-raw-int; audio/x-raw-float')
        self._decodebin = gst.element_factory_make('decodebin2')
        self._decodebin.set_property('caps', audio_caps)
        self._decodebin.connect('pad-added', pad_added)

        self._pipe = gst.element_factory_make('pipeline')
        self._pipe.add(self._typefinder)
        self._pipe.add(self._decodebin)
        self._pipe.add(sink)

        self._typefinder.link(self._decodebin)

        self._bus = self._pipe.get_bus()

    def scan(self, uri):
        """
        Scan the given uri collecting relevant metadata.

        :param uri: URI of the resource to scan.
        :type event: string
        :return: A named tuple containing
            ``(uri, tags, duration, seekable, mime)``.
            ``tags`` is a dictionary of lists for all the tags we found.
            ``duration`` is the length of the URI in milliseconds, or
            :class:`None` if the URI has no duration. ``seekable`` is boolean.
            indicating if a seek would succeed.
        """
        tags, duration, seekable, mime = None, None, None, None
        try:
            self._setup(uri)
            tags, mime = self._collect()
            duration = self._query_duration()
            seekable = self._query_seekable()
        finally:
            self._reset()

        return Result(uri, tags, duration, seekable, mime)

    def _setup(self, uri):
        """Primes the pipeline for collection."""
        protocol = gst.uri_get_protocol(uri)
        if self._src and protocol not in self._src.get_protocols():
            self._src.unlink(self._typefinder)
            self._pipe.remove(self._src)
            self._src = None

        if not self._src:
            self._src = gst.element_make_from_uri(gst.URI_SRC, uri)
            if not self._src:
                raise exceptions.ScannerError('Could not find any elements to '
                                              'handle %s URI.' % protocol)
            utils.setup_proxy(self._src, self._proxy_config)
            self._pipe.add(self._src)
            self._src.link(self._typefinder)

        self._pipe.set_state(gst.STATE_READY)
        self._src.set_uri(uri)

        result = self._pipe.set_state(gst.STATE_PAUSED)
        if result == gst.STATE_CHANGE_NO_PREROLL:
            # Live sources don't pre-roll, so set to playing to get data.
            self._pipe.set_state(gst.STATE_PLAYING)

    def _collect(self):
        """Polls for messages to collect data."""
        start = time.time()
        timeout_s = self._timeout_ms / 1000.0
        tags, mime, missing_description = {}, None, None

        while time.time() - start < timeout_s:
            if not self._bus.have_pending():
                continue
            message = self._bus.pop()

            if message.type == gst.MESSAGE_ELEMENT:
                if gst.pbutils.is_missing_plugin_message(message):
                    missing_description = encoding.locale_decode(
                        _missing_plugin_desc(message))
            elif message.type == gst.MESSAGE_APPLICATION:
                mime = message.structure.get_name()
                if mime.startswith('text/') or mime == 'application/xml':
                    return tags, mime
            elif message.type == gst.MESSAGE_ERROR:
                error = encoding.locale_decode(message.parse_error()[0])
                if missing_description:
                    error = '%s (%s)' % (missing_description, error)
                raise exceptions.ScannerError(error)
            elif message.type == gst.MESSAGE_EOS:
                return tags, mime
            elif message.type == gst.MESSAGE_ASYNC_DONE:
                if message.src == self._pipe:
                    return tags, mime
            elif message.type == gst.MESSAGE_TAG:
                taglist = message.parse_tag()
                # Note that this will only keep the last tag.
                tags.update(utils.convert_taglist(taglist))

        raise exceptions.ScannerError('Timeout after %dms' % self._timeout_ms)

    def _reset(self):
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

    def _query_seekable(self):
        query = gst.query_new_seeking(gst.FORMAT_TIME)
        self._pipe.query(query)
        return query.parse_seeking()[1]
