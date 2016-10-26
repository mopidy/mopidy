from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import collections
import logging
import time

from mopidy import exceptions
from mopidy.audio import tags as tags_lib, utils
from mopidy.internal import encoding, log
from mopidy.internal.gi import Gst, GstPbutils

# GST_ELEMENT_FACTORY_LIST:
_DECODER = 1 << 0
_AUDIO = 1 << 50
_DEMUXER = 1 << 5
_DEPAYLOADER = 1 << 8
_PARSER = 1 << 6

# GST_TYPE_AUTOPLUG_SELECT_RESULT:
_SELECT_TRY = 0
_SELECT_EXPOSE = 1

_Result = collections.namedtuple(
    'Result', ('uri', 'tags', 'duration', 'seekable', 'mime', 'playable'))

logger = logging.getLogger(__name__)


def _trace(*args, **kwargs):
    logger.log(log.TRACE_LOG_LEVEL, *args, **kwargs)


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
        pipeline, signals = _setup_pipeline(uri, self._proxy_config)

        try:
            _start_pipeline(pipeline)
            tags, mime, have_audio, duration = _process(pipeline, timeout)
            seekable = _query_seekable(pipeline)
        finally:
            signals.clear()
            pipeline.set_state(Gst.State.NULL)
            del pipeline

        return _Result(uri, tags, duration, seekable, mime, have_audio)


# Turns out it's _much_ faster to just create a new pipeline for every as
# decodebins and other elements don't seem to take well to being reused.
def _setup_pipeline(uri, proxy_config=None):
    src = Gst.Element.make_from_uri(Gst.URIType.SRC, uri)
    if not src:
        raise exceptions.ScannerError('GStreamer can not open: %s' % uri)

    if proxy_config:
        utils.setup_proxy(src, proxy_config)

    signals = utils.Signals()
    pipeline = Gst.ElementFactory.make('pipeline')
    pipeline.add(src)

    if _has_src_pads(src):
        _setup_decodebin(src, src.get_static_pad('src'), pipeline, signals)
    elif _has_dynamic_src_pad(src):
        signals.connect(src, 'pad-added', _setup_decodebin, pipeline, signals)
    else:
        raise exceptions.ScannerError('No pads found in source element.')

    return pipeline, signals


def _has_src_pads(element):
    pads = []
    element.iterate_src_pads().foreach(pads.append)
    return bool(pads)


def _has_dynamic_src_pad(element):
    for template in element.get_pad_template_list():
        if template.direction == Gst.PadDirection.SRC:
            if template.presence == Gst.PadPresence.SOMETIMES:
                return True
    return False


def _setup_decodebin(element, pad, pipeline, signals):
    typefind = Gst.ElementFactory.make('typefind')
    decodebin = Gst.ElementFactory.make('decodebin')

    for element in (typefind, decodebin):
        pipeline.add(element)
        element.sync_state_with_parent()

    pad.link(typefind.get_static_pad('sink'))
    typefind.link(decodebin)

    signals.connect(typefind, 'have-type', _have_type, decodebin)
    signals.connect(decodebin, 'pad-added', _pad_added, pipeline)
    signals.connect(decodebin, 'autoplug-select', _autoplug_select)


def _have_type(element, probability, caps, decodebin):
    decodebin.set_property('sink-caps', caps)
    struct = Gst.Structure.new_empty('have-type')
    struct.set_value('caps', caps.get_structure(0))
    element.get_bus().post(Gst.Message.new_application(element, struct))


def _pad_added(element, pad, pipeline):
    sink = Gst.ElementFactory.make('fakesink')
    sink.set_property('sync', False)

    pipeline.add(sink)
    sink.sync_state_with_parent()
    pad.link(sink.get_static_pad('sink'))

    if pad.query_caps().is_subset(Gst.Caps.from_string('audio/x-raw')):
        # Probably won't happen due to autoplug-select fix, but lets play it
        # safe until we've tested more.
        struct = Gst.Structure.new_empty('have-audio')
        element.get_bus().post(Gst.Message.new_application(element, struct))


def _autoplug_select(element, pad, caps, factory):
    if factory.list_is_type(_DECODER | _AUDIO):
        struct = Gst.Structure.new_empty('have-audio')
        element.get_bus().post(Gst.Message.new_application(element, struct))
    if not factory.list_is_type(_DEMUXER | _DEPAYLOADER | _PARSER):
        return _SELECT_EXPOSE
    return _SELECT_TRY


def _start_pipeline(pipeline):
    result = pipeline.set_state(Gst.State.PAUSED)
    if result == Gst.StateChangeReturn.NO_PREROLL:
        pipeline.set_state(Gst.State.PLAYING)


def _query_duration(pipeline):
    success, duration = pipeline.query_duration(Gst.Format.TIME)
    if not success:
        duration = None  # Make sure error case preserves None.
    elif duration < 0:
        duration = None  # Stream without duration.
    else:
        duration = duration // Gst.MSECOND
    return success, duration


def _query_seekable(pipeline):
    query = Gst.Query.new_seeking(Gst.Format.TIME)
    pipeline.query(query)
    return query.parse_seeking()[1]


def _process(pipeline, timeout_ms):
    bus = pipeline.get_bus()
    tags = {}
    mime = None
    have_audio = False
    missing_message = None
    duration = None

    types = (
        Gst.MessageType.ELEMENT |
        Gst.MessageType.APPLICATION |
        Gst.MessageType.ERROR |
        Gst.MessageType.EOS |
        Gst.MessageType.ASYNC_DONE |
        Gst.MessageType.DURATION_CHANGED |
        Gst.MessageType.TAG
    )

    timeout = timeout_ms
    start = int(time.time() * 1000)
    while timeout > 0:
        msg = bus.timed_pop_filtered(timeout * Gst.MSECOND, types)
        if msg is None:
            break

        if logger.isEnabledFor(log.TRACE_LOG_LEVEL) and msg.get_structure():
            debug_text = msg.get_structure().to_string()
            if len(debug_text) > 77:
                debug_text = debug_text[:77] + '...'
            _trace('element %s: %s', msg.src.get_name(), debug_text)

        if msg.type == Gst.MessageType.ELEMENT:
            if GstPbutils.is_missing_plugin_message(msg):
                missing_message = msg
        elif msg.type == Gst.MessageType.APPLICATION:
            if msg.get_structure().get_name() == 'have-type':
                mime = msg.get_structure().get_value('caps').get_name()
                if mime and (
                        mime.startswith('text/') or mime == 'application/xml'):
                    return tags, mime, have_audio, duration
            elif msg.get_structure().get_name() == 'have-audio':
                have_audio = True
        elif msg.type == Gst.MessageType.ERROR:
            error = encoding.locale_decode(msg.parse_error()[0])
            if missing_message and not mime:
                caps = missing_message.get_structure().get_value('detail')
                mime = caps.get_structure(0).get_name()
                return tags, mime, have_audio, duration
            raise exceptions.ScannerError(error)
        elif msg.type == Gst.MessageType.EOS:
            return tags, mime, have_audio, duration
        elif msg.type == Gst.MessageType.ASYNC_DONE:
            success, duration = _query_duration(pipeline)
            if tags and success:
                return tags, mime, have_audio, duration

            # Don't try workaround for non-seekable sources such as mmssrc:
            if not _query_seekable(pipeline):
                return tags, mime, have_audio, duration

            # Workaround for upstream bug which causes tags/duration to arrive
            # after pre-roll. We get around this by starting to play the track
            # and then waiting for a duration change.
            # https://bugzilla.gnome.org/show_bug.cgi?id=763553
            logger.debug('Using workaround for duration missing before play.')
            result = pipeline.set_state(Gst.State.PLAYING)
            if result == Gst.StateChangeReturn.FAILURE:
                return tags, mime, have_audio, duration

        elif msg.type == Gst.MessageType.DURATION_CHANGED and tags:
            # VBR formats sometimes seem to not have a duration by the time we
            # go back to paused. So just try to get it right away.
            success, duration = _query_duration(pipeline)
            pipeline.set_state(Gst.State.PAUSED)
            if success:
                return tags, mime, have_audio, duration
        elif msg.type == Gst.MessageType.TAG:
            taglist = msg.parse_tag()
            # Note that this will only keep the last tag.
            tags.update(tags_lib.convert_taglist(taglist))

        timeout = timeout_ms - (int(time.time() * 1000) - start)

    raise exceptions.ScannerError('Timeout after %dms' % timeout_ms)


if __name__ == '__main__':
    import os
    import sys

    from mopidy.internal import path

    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s',
                        level=log.TRACE_LOG_LEVEL)

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
                line = '%-20s   %s' % (tag, value)
                if len(line) > 77:
                    line = line[:77] + '...'
                print(line)
        except exceptions.ScannerError as error:
            print('%s: %s' % (uri, error))
