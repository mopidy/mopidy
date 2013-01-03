from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst


def calculate_duration(num_samples, sample_rate):
    """Determine duration of samples using GStreamer helper for precise
    math."""
    return gst.util_uint64_scale(num_samples, gst.SECOND, sample_rate)


def create_buffer(data, capabilites=None, timestamp=None, duration=None):
    """Create a new GStreamer buffer based on provided data.

    Mainly intended to keep gst imports out of non-audio modules.
    """
    buffer_ = gst.Buffer(data)
    if capabilites:
        if isinstance(capabilites, basestring):
            capabilites = gst.caps_from_string(capabilites)
        buffer_.set_caps(capabilites)
    if timestamp:
        buffer_.timestamp = timestamp
    if duration:
        buffer_.duration = duration
    return buffer_


def millisecond_to_clocktime(value):
    """Convert a millisecond time to internal GStreamer time."""
    return value * gst.MSECOND


def clocktime_to_millisecond(value):
    """Convert an internal GStreamer time to millisecond time."""
    return value // gst.MSECOND


def supported_uri_schemes(uri_schemes):
    """Determine which URIs we can actually support from provided whitelist.

    :param uri_schemes: list/set of URIs to check support for.
    :type uri_schemes: list or set or URI schemes as strings.
    :rtype: set of URI schemes we can support via this GStreamer install.
    """
    supported_schemes = set()
    registry = gst.registry_get_default()

    for factory in registry.get_feature_list(gst.TYPE_ELEMENT_FACTORY):
        for uri in factory.get_uri_protocols():
            if uri in uri_schemes:
                supported_schemes.add(uri)

    return supported_schemes
