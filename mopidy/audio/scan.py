from __future__ import absolute_import, division, unicode_literals

import collections

import pygst
pygst.require('0.10')
import gst  # noqa
import gst.pbutils

from mopidy import exceptions
from mopidy.audio import utils
from mopidy.utils import encoding

_missing_plugin_desc = gst.pbutils.missing_plugin_message_get_description

_Result = collections.namedtuple(
    'Result', ('uri', 'tags', 'duration', 'seekable', 'mime'))

_RAW_AUDIO = gst.Caps(b'audio/x-raw-int; audio/x-raw-float')


# TODO: replace with a scan(uri, timeout=1000, proxy_config=None)?
class Scanner(object):
    """
    Helper to get tags and other relevant info from URIs.

    :param timeout: timeout for scanning a URI in ms
    :param proxy_config: dictionary containing proxy config strings.
    :type event: int
    """

    def __init__(self, timeout=1000, proxy_config=None):
        self._timeout_ms = int(timeout)
        self._proxy_config = proxy_config or {}

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
        pipeline = _setup_pipeline(uri, self._proxy_config)

        try:
            _start_pipeline(pipeline)
            tags, mime = _process(pipeline, self._timeout_ms)
            duration = _query_duration(pipeline)
            seekable = _query_seekable(pipeline)
        finally:
            pipeline.set_state(gst.STATE_NULL)
            del pipeline

        return _Result(uri, tags, duration, seekable, mime)


# Turns out it's _much_ faster to just create a new pipeline for every as
# decodebins and other elements don't seem to take well to being reused.
def _setup_pipeline(uri, proxy_config=None):
    src = gst.element_make_from_uri(gst.URI_SRC, uri)
    if not src:
        raise exceptions.ScannerError('GStreamer can not open: %s' % uri)

    typefind = gst.element_factory_make('typefind')
    decodebin = gst.element_factory_make('decodebin2')
    sink = gst.element_factory_make('fakesink')

    pipeline = gst.element_factory_make('pipeline')
    pipeline.add_many(src, typefind, decodebin, sink)
    gst.element_link_many(src, typefind, decodebin)

    if proxy_config:
        utils.setup_proxy(src, proxy_config)

    decodebin.set_property('caps', _RAW_AUDIO)
    decodebin.connect('pad-added', _pad_added, sink)
    typefind.connect('have-type', _have_type, decodebin)

    return pipeline


def _have_type(element, probability, caps, decodebin):
    decodebin.set_property('sink-caps', caps)
    msg = gst.message_new_application(element, caps.get_structure(0))
    element.get_bus().post(msg)


def _pad_added(element, pad, sink):
    return pad.link(sink.get_pad('sink'))


def _start_pipeline(pipeline):
    if pipeline.set_state(gst.STATE_PAUSED) == gst.STATE_CHANGE_NO_PREROLL:
        pipeline.set_state(gst.STATE_PLAYING)


def _query_duration(pipeline):
    try:
        duration = pipeline.query_duration(gst.FORMAT_TIME, None)[0]
    except gst.QueryError:
        return None

    if duration < 0:
        return None
    else:
        return duration // gst.MSECOND


def _query_seekable(pipeline):
    query = gst.query_new_seeking(gst.FORMAT_TIME)
    pipeline.query(query)
    return query.parse_seeking()[1]


def _process(pipeline, timeout_ms):
    clock = pipeline.get_clock()
    bus = pipeline.get_bus()
    timeout = timeout_ms * gst.MSECOND
    tags, mime, missing_description = {}, None, None

    types = (gst.MESSAGE_ELEMENT | gst.MESSAGE_APPLICATION | gst.MESSAGE_ERROR
             | gst.MESSAGE_EOS | gst.MESSAGE_ASYNC_DONE | gst.MESSAGE_TAG)

    start = clock.get_time()
    while timeout > 0:
        message = bus.timed_pop_filtered(timeout, types)

        if message is None:
            break
        elif message.type == gst.MESSAGE_ELEMENT:
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
            if message.src == pipeline:
                return tags, mime
        elif message.type == gst.MESSAGE_TAG:
            taglist = message.parse_tag()
            # Note that this will only keep the last tag.
            tags.update(utils.convert_taglist(taglist))

        timeout -= clock.get_time() - start

    raise exceptions.ScannerError('Timeout after %dms' % timeout_ms)
