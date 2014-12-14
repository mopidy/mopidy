from __future__ import absolute_import, unicode_literals

import datetime
import logging
import numbers

import pygst
pygst.require('0.10')
import gst  # noqa

from mopidy import compat

logger = logging.getLogger(__name__)


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
        if isinstance(capabilites, compat.string_types):
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


def convert_taglist(taglist):
    """Convert a :class:`gst.Taglist` to plain python types.

    Knows how to convert:
     - Dates
     - Buffers
     - Numbers
     - Strings
     - Booleans

    Unknown types will be ignored and debug logged. Tag keys are all strings
    defined by GStreamer.

    :param :class:`gst.Taglist` taglist: A GStreamer taglist to be converted.
    :rtype: dictionary of tag keys with a list of values.
    """
    result = {}

    # Taglists are not really dicts, hence the lack of .items() and
    # explicit use of .keys()
    for key in taglist.keys():
        result.setdefault(key, [])

        values = taglist[key]
        if not isinstance(values, list):
            values = [values]

        for value in values:
            if isinstance(value, gst.Date):
                try:
                    date = datetime.date(value.year, value.month, value.day)
                    result[key].append(date)
                except ValueError:
                    logger.debug('Ignoring invalid date: %r = %r', key, value)
            elif isinstance(value, gst.Buffer):
                result[key].append(bytes(value))
            elif isinstance(value, (basestring, bool, numbers.Number)):
                result[key].append(value)
            else:
                logger.debug('Ignoring unknown data: %r = %r', key, value)

    return result
