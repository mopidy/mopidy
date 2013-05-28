from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst

import xml.dom.pulldom


# TODO: make detect_FOO_header reusable in general mopidy code.
# i.e. give it just a "peek" like function.
def detect_m3u_header(typefind):
    return typefind.peek(0, 8) == b'#EXTM3U\n'


def detect_pls_header(typefind):
    print repr(typefind.peek(0, 11) == b'[playlist]\n')
    return typefind.peek(0, 11) == b'[playlist]\n'


def detect_xspf_header(typefind):
    # Get more data than the 90 needed for header in case spacing is funny.
    data = typefind.peek(0, 150)

    # Bail early if the words xml and playlist are not present.
    if not data or b'xml' not in data or b'playlist' not in data:
        return False

    # TODO: handle parser errors.
    # Try parsing what we have, bailing on first element.
    for event, node in xml.dom.pulldom.parseString(data):
        if event == xml.dom.pulldom.START_ELEMENT:
            return (node.tagName == 'playlist' and
                    node.node.namespaceURI == 'http://xspf.org/ns/0/')
    return False


def playlist_typefinder(typefind, func, caps):
    if func(typefind):
        typefind.suggest(gst.TYPE_FIND_MAXIMUM, caps)


def register_typefind(mimetype, func, extensions):
    caps = gst.caps_from_string(mimetype)
    gst.type_find_register(mimetype, gst.RANK_PRIMARY, playlist_typefinder,
                           extensions, caps, func, caps)


def register_typefinders():
    register_typefind('audio/x-mpegurl', detect_m3u_header, [b'm3u', b'm3u8'])
    register_typefind('audio/x-scpls', detect_pls_header, [b'pls'])
    register_typefind('application/xspf+xml', detect_xspf_header, [b'xspf'])
