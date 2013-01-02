from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst


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
