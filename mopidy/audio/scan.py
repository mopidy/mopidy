from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import collections

import pygst
pygst.require('0.10')
import gst  # noqa
import gst.pbutils  # noqa

from mopidy import exceptions
from mopidy.audio import utils
from mopidy.internal import encoding

_Result = collections.namedtuple(
    'Result', ('uri', 'tags', 'duration', 'seekable', 'mime', 'playable'))

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
            tags, mime, have_audio = _process(pipeline, self._timeout_ms)
            duration = _query_duration(pipeline)
            seekable = _query_seekable(pipeline)
        finally:
            pipeline.set_state(gst.STATE_NULL)
            del pipeline

        return _Result(uri, tags, duration, seekable, mime, have_audio)


# Turns out it's _much_ faster to just create a new pipeline for every as
# decodebins and other elements don't seem to take well to being reused.
def _setup_pipeline(uri, proxy_config=None):
    src = gst.element_make_from_uri(gst.URI_SRC, uri)
    if not src:
        raise exceptions.ScannerError('GStreamer can not open: %s' % uri)

    typefind = gst.element_factory_make('typefind')
    decodebin = gst.element_factory_make('decodebin2')

    pipeline = gst.element_factory_make('pipeline')
    for e in (src, typefind, decodebin):
        pipeline.add(e)
    gst.element_link_many(src, typefind, decodebin)

    if proxy_config:
        utils.setup_proxy(src, proxy_config)

    typefind.connect('have-type', _have_type, decodebin)
    decodebin.connect('pad-added', _pad_added, pipeline)

    return pipeline


def _have_type(element, probability, caps, decodebin):
    decodebin.set_property('sink-caps', caps)
    struct = gst.Structure('have-type')
    struct['caps'] = caps.get_structure(0)
    element.get_bus().post(gst.message_new_application(element, struct))


def _pad_added(element, pad, pipeline):
    sink = gst.element_factory_make('fakesink')
    sink.set_property('sync', False)

    pipeline.add(sink)
    sink.sync_state_with_parent()
    pad.link(sink.get_pad('sink'))

    if pad.get_caps().is_subset(_RAW_AUDIO):
        struct = gst.Structure('have-audio')
        element.get_bus().post(gst.message_new_application(element, struct))


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
    tags, mime, have_audio, missing_message = {}, None, False, None

    types = (gst.MESSAGE_ELEMENT | gst.MESSAGE_APPLICATION | gst.MESSAGE_ERROR
             | gst.MESSAGE_EOS | gst.MESSAGE_ASYNC_DONE | gst.MESSAGE_TAG)

    previous = clock.get_time()
    while timeout > 0:
        message = bus.timed_pop_filtered(timeout, types)

        if message is None:
            break
        elif message.type == gst.MESSAGE_ELEMENT:
            if gst.pbutils.is_missing_plugin_message(message):
                missing_message = message
        elif message.type == gst.MESSAGE_APPLICATION:
            if message.structure.get_name() == 'have-type':
                mime = message.structure['caps'].get_name()
                if mime.startswith('text/') or mime == 'application/xml':
                    return tags, mime, have_audio
            elif message.structure.get_name() == 'have-audio':
                have_audio = True
        elif message.type == gst.MESSAGE_ERROR:
            error = encoding.locale_decode(message.parse_error()[0])
            if missing_message and not mime:
                caps = missing_message.structure['detail']
                mime = caps.get_structure(0).get_name()
                return tags, mime, have_audio
            raise exceptions.ScannerError(error)
        elif message.type == gst.MESSAGE_EOS:
            return tags, mime, have_audio
        elif message.type == gst.MESSAGE_ASYNC_DONE:
            if message.src == pipeline:
                return tags, mime, have_audio
        elif message.type == gst.MESSAGE_TAG:
            taglist = message.parse_tag()
            # Note that this will only keep the last tag.
            tags.update(utils.convert_taglist(taglist))

        now = clock.get_time()
        timeout -= now - previous
        previous = now

    raise exceptions.ScannerError('Timeout after %dms' % timeout_ms)


if __name__ == '__main__':
    import os
    import sys

    import gobject

    from mopidy.internal import path

    gobject.threads_init()

    scanner = Scanner(5000)
    for uri in sys.argv[1:]:
        if not gst.uri_is_valid(uri):
            uri = path.path_to_uri(os.path.abspath(uri))
        try:
            result = scanner.scan(uri)
            for key in ('uri', 'mime', 'duration', 'playable', 'seekable'):
                print('%-20s   %s' % (key, getattr(result, key)))
            print('tags')
            for tag, value in result.tags.items():
                print('%-20s   %s' % (tag, value))
        except exceptions.ScannerError as error:
            print('%s: %s' % (uri, error))
