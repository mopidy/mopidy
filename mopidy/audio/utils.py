from __future__ import absolute_import, unicode_literals

from mopidy import httpclient
from mopidy.internal.gi import Gst


def calculate_duration(num_samples, sample_rate):
    """Determine duration of samples using GStreamer helper for precise
    math."""
    return Gst.util_uint64_scale(num_samples, Gst.SECOND, sample_rate)


def create_buffer(data, timestamp=None, duration=None):
    """Create a new GStreamer buffer based on provided data.

    Mainly intended to keep gst imports out of non-audio modules.

    .. versionchanged:: 2.0
        ``capabilites`` argument was removed.
    """
    if not data:
        raise ValueError('Cannot create buffer without data')
    buffer_ = Gst.Buffer.new_wrapped(data)
    if timestamp is not None:
        buffer_.pts = timestamp
    if duration is not None:
        buffer_.duration = duration
    return buffer_


def millisecond_to_clocktime(value):
    """Convert a millisecond time to internal GStreamer time."""
    return value * Gst.MSECOND


def clocktime_to_millisecond(value):
    """Convert an internal GStreamer time to millisecond time."""
    return value // Gst.MSECOND


def supported_uri_schemes(uri_schemes):
    """Determine which URIs we can actually support from provided whitelist.

    :param uri_schemes: list/set of URIs to check support for.
    :type uri_schemes: list or set or URI schemes as strings.
    :rtype: set of URI schemes we can support via this GStreamer install.
    """
    supported_schemes = set()
    registry = Gst.Registry.get()

    for factory in registry.get_feature_list(Gst.ElementFactory):
        for uri in factory.get_uri_protocols():
            if uri in uri_schemes:
                supported_schemes.add(uri)

    return supported_schemes


def setup_proxy(element, config):
    """Configure a GStreamer element with proxy settings.

    :param element: element to setup proxy in.
    :type element: :class:`Gst.GstElement`
    :param config: proxy settings to use.
    :type config: :class:`dict`
    """
    if not hasattr(element.props, 'proxy') or not config.get('hostname'):
        return

    element.set_property('proxy', httpclient.format_proxy(config, auth=False))
    element.set_property('proxy-id', config.get('username'))
    element.set_property('proxy-pw', config.get('password'))


class Signals(object):

    """Helper for tracking gobject signal registrations"""

    def __init__(self):
        self._ids = {}

    def connect(self, element, event, func, *args):
        """Connect a function + args to signal event on an element.

        Each event may only be handled by one callback in this implementation.
        """
        assert (element, event) not in self._ids
        self._ids[(element, event)] = element.connect(event, func, *args)

    def disconnect(self, element, event):
        """Disconnect whatever handler we have for an element+event pair.

        Does nothing it the handler has already been removed.
        """
        signal_id = self._ids.pop((element, event), None)
        if signal_id is not None:
            element.disconnect(signal_id)

    def clear(self):
        """Clear all registered signal handlers."""
        for element, event in self._ids.keys():
            element.disconnect(self._ids.pop((element, event)))
