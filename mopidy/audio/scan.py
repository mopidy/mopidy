from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import collections

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GstPbutils

from mopidy import exceptions
from mopidy.audio import utils
from mopidy.internal import encoding

_Result = collections.namedtuple(
    'Result', ('uri', 'tags', 'duration', 'seekable', 'mime', 'playable'))

_RAW_AUDIO = Gst.Caps(b'audio/x-raw-int; audio/x-raw-float')


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

    def scan(self, uri, timeout=None):
        """
        Scan the given uri collecting relevant metadata.

        :param uri: URI of the resource to scan.
        :type uri: string
        :param timeout: timeout for scanning a URI in ms. Defaults to the
            ``timeout`` value used when creating the scanner.
        :type timeout: int
        :return: A named tuple containing
            ``(uri, tags, duration, seekable, mime)``.
            ``tags`` is a dictionary of lists for all the tags we found.
            ``duration`` is the length of the URI in milliseconds, or
            :class:`None` if the URI has no duration. ``seekable`` is boolean.
            indicating if a seek would succeed.
        """
        timeout = int(timeout or self._timeout_ms)
        tags, duration, seekable, mime = None, None, None, None
        pipeline = _setup_pipeline(uri, self._proxy_config)

        try:
            _start_pipeline(pipeline)
            tags, mime, have_audio = _process(pipeline, timeout)
            duration = _query_duration(pipeline)
            seekable = _query_seekable(pipeline)
        finally:
            pipeline.set_state(Gst.State.NULL)
            del pipeline

        return _Result(uri, tags, duration, seekable, mime, have_audio)


# Turns out it's _much_ faster to just create a new pipeline for every as
# decodebins and other elements don't seem to take well to being reused.
def _setup_pipeline(uri, proxy_config=None):
    src = Gst.element_make_from_uri(Gst.URI_SRC, uri)
    if not src:
        raise exceptions.ScannerError('GStreamer can not open: %s' % uri)

    typefind = Gst.ElementFactory.make('typefind')
    decodebin = Gst.ElementFactory.make('decodebin2')

    pipeline = Gst.ElementFactory.make('pipeline')
    for e in (src, typefind, decodebin):
        pipeline.add(e)
    src.link(typefind)
    typefind.link(decodebin)

    if proxy_config:
        utils.setup_proxy(src, proxy_config)

    typefind.connect('have-type', _have_type, decodebin)
    decodebin.connect('pad-added', _pad_added, pipeline)

    return pipeline


def _have_type(element, probability, caps, decodebin):
    decodebin.set_property('sink-caps', caps)
    struct = Gst.Structure('have-type')
    struct['caps'] = caps.get_structure(0)
    element.get_bus().post(Gst.message_new_application(element, struct))


def _pad_added(element, pad, pipeline):
    sink = Gst.ElementFactory.make('fakesink')
    sink.set_property('sync', False)

    pipeline.add(sink)
    sink.sync_state_with_parent()
    pad.link(sink.get_pad('sink'))

    if pad.query_caps().is_subset(_RAW_AUDIO):
        struct = Gst.Structure('have-audio')
        element.get_bus().post(Gst.message_new_application(element, struct))


def _start_pipeline(pipeline):
    if pipeline.set_state(Gst.State.PAUSED) == Gst.State.CHANGE_NO_PREROLL:
        pipeline.set_state(Gst.State.PLAYING)


def _query_duration(pipeline):
    try:
        duration = pipeline.query_duration(Gst.Format.TIME, None)[0]
    except Gst.QueryError:
        return None

    if duration < 0:
        return None
    else:
        return duration // Gst.MSECOND


def _query_seekable(pipeline):
    query = Gst.query_new_seeking(Gst.Format.TIME)
    pipeline.query(query)
    return query.parse_seeking()[1]


def _process(pipeline, timeout_ms):
    clock = pipeline.get_clock()
    bus = pipeline.get_bus()
    timeout = timeout_ms * Gst.MSECOND
    tags = {}
    mime = None
    have_audio = False
    missing_message = None

    types = (
        Gst.MESSAGE_ELEMENT | Gst.MESSAGE_APPLICATION | Gst.MESSAGE_ERROR |
        Gst.MESSAGE_EOS | Gst.MESSAGE_ASYNC_DONE | Gst.MESSAGE_TAG)

    previous = clock.get_time()
    while timeout > 0:
        message = bus.timed_pop_filtered(timeout, types)

        if message is None:
            break
        elif message.type == Gst.MESSAGE_ELEMENT:
            if GstPbutils.is_missing_plugin_message(message):
                missing_message = message
        elif message.type == Gst.MESSAGE_APPLICATION:
            if message.structure.get_name() == 'have-type':
                mime = message.structure['caps'].get_name()
                if mime.startswith('text/') or mime == 'application/xml':
                    return tags, mime, have_audio
            elif message.structure.get_name() == 'have-audio':
                have_audio = True
        elif message.type == Gst.MESSAGE_ERROR:
            error = encoding.locale_decode(message.parse_error()[0])
            if missing_message and not mime:
                caps = missing_message.structure['detail']
                mime = caps.get_structure(0).get_name()
                return tags, mime, have_audio
            raise exceptions.ScannerError(error)
        elif message.type == Gst.MESSAGE_EOS:
            return tags, mime, have_audio
        elif message.type == Gst.MESSAGE_ASYNC_DONE:
            if message.src == pipeline:
                return tags, mime, have_audio
        elif message.type == Gst.MESSAGE_TAG:
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

    from mopidy.internal import path

    GObject.threads_init()
    Gst.init()

    scanner = Scanner(5000)
    for uri in sys.argv[1:]:
        if not Gst.uri_is_valid(uri):
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
