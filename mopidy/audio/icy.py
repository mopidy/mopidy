from __future__ import absolute_import, unicode_literals

import gobject

import pygst
pygst.require('0.10')
import gst  # noqa


class IcySrc(gst.Bin, gst.URIHandler):
    __gstdetails__ = ('IcySrc',
                      'Src',
                      'HTTP src wrapper for icy:// support.',
                      'Mopidy')

    srcpad_template = gst.PadTemplate(
        'src', gst.PAD_SRC, gst.PAD_ALWAYS,
        gst.caps_new_any())

    __gsttemplates__ = (srcpad_template,)

    def __init__(self):
        super(IcySrc, self).__init__()
        self._httpsrc = gst.element_make_from_uri(gst.URI_SRC, 'http://')
        try:
            self._httpsrc.set_property('iradio-mode', True)
        except TypeError:
            pass
        self.add(self._httpsrc)

        self._srcpad = gst.GhostPad('src', self._httpsrc.get_pad('src'))
        self.add_pad(self._srcpad)

    @classmethod
    def do_get_type_full(cls):
        return gst.URI_SRC

    @classmethod
    def do_get_protocols_full(cls):
        return [b'icy', b'icyx']

    def do_set_uri(self, uri):
        if uri.startswith('icy://'):
            return self._httpsrc.set_uri(b'http://' + uri[len('icy://'):])
        elif uri.startswith('icyx://'):
            return self._httpsrc.set_uri(b'https://' + uri[len('icyx://'):])
        else:
            return False

    def do_get_uri(self):
        uri = self._httpsrc.get_uri()
        if uri.startswith('http://'):
            return b'icy://' + uri[len('http://'):]
        else:
            return b'icyx://' + uri[len('https://'):]


def register():
    # Only register icy if gst install can't handle it on it's own.
    if not gst.element_make_from_uri(gst.URI_SRC, 'icy://'):
        gobject.type_register(IcySrc)
        gst.element_register(
            IcySrc, IcySrc.__name__.lower(), gst.RANK_MARGINAL)
