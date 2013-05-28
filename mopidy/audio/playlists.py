from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst
import gobject

import ConfigParser as configparser
import io
import xml.etree.ElementTree
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


def parse_m3u(data):
    # TODO: convert non uris to file uris.
    for line in data.readlines():
        if not line.startswith('#') and line.strip():
            yield line


def parse_pls(data):
    # TODO: error handling of bad playlists.
    # TODO: convert non uris to file uris.
    cp = configparser.RawConfigParser()
    cp.readfp(data)
    for i in xrange(1, cp.getint('playlist', 'numberofentries')):
        yield cp.get('playlist', 'file%d' % i)


def parse_xspf(data):
    # TODO: handle parser errors
    root = xml.etree.ElementTree.fromstring(data.read())
    tracklist = tree.find('{http://xspf.org/ns/0/}trackList')
    for track in tracklist.findall('{http://xspf.org/ns/0/}track'):
        yield track.findtext('{http://xspf.org/ns/0/}location')


def parse_urilist(data):
    for line in data.readlines():
        if not line.startswith('#') and line.strip():
            yield line


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


class BasePlaylistElement(gst.Bin):
    sinktemplate = None
    srctemplate = None
    ghostsrc = False

    def __init__(self):
        super(BasePlaylistElement, self).__init__()
        self._data = io.BytesIO()
        self._done = False

        self.sink = gst.Pad(self.sinktemplate)
        self.sink.set_chain_function(self._chain)
        self.sink.set_event_function(self._event)
        self.add_pad(self.sink)

        if self.ghostsrc:
            self.src = gst.ghost_pad_new_notarget('src', gst.PAD_SRC)
        else:
            self.src = gst.Pad(self.srctemplate)
        self.add_pad(self.src)

    def convert(self, data):
        raise NotImplementedError

    def handle(self, uris):
        self.src.push(gst.Buffer('\n'.join(uris)))
        return False

    def _chain(self, pad, buf):
        if not self._done:
            self._data.write(buf.data)
            return gst.FLOW_OK
        return gst.FLOW_EOS

    def _event(self, pad, event):
        if event.type == gst.EVENT_NEWSEGMENT:
            return True

        if event.type == gst.EVENT_EOS:
            self._done = True
            self._data.seek(0)
            if self.handle(list(self.convert(self._data))):
                return True
        return pad.event_default(event)


class M3UDecoder(BasePlaylistElement):
    __gstdetails__ = ('M3U Decoder',
                      'Decoder',
                      'Convert .m3u to text/uri-list',
                      'Mopidy')

    sinktemplate = gst.PadTemplate ('sink',
        gst.PAD_SINK,
        gst.PAD_ALWAYS,
        gst.caps_from_string('audio/x-mpegurl'))

    srctemplate = gst.PadTemplate ('src',
        gst.PAD_SRC,
        gst.PAD_ALWAYS,
        gst.caps_from_string('text/uri-list'))

    __gsttemplates__ = (sinktemplate, srctemplate)

    def convert(self, data):
        return parse_m3u(data)


class PLSDecoder(BasePlaylistElement):
    __gstdetails__ = ('PLS Decoder',
                      'Decoder',
                      'Convert .pls to text/uri-list',
                      'Mopidy')

    sinktemplate = gst.PadTemplate ('sink',
        gst.PAD_SINK,
        gst.PAD_ALWAYS,
        gst.caps_from_string('audio/x-scpls'))

    srctemplate = gst.PadTemplate ('src',
        gst.PAD_SRC,
        gst.PAD_ALWAYS,
        gst.caps_from_string('text/uri-list'))

    __gsttemplates__ = (sinktemplate, srctemplate)

    def convert(self, data):
        return parse_pls(data)


class XSPFDecoder(BasePlaylistElement):
    __gstdetails__ = ('XSPF Decoder',
                      'Decoder',
                      'Convert .pls to text/uri-list',
                      'Mopidy')

    sinktemplate = gst.PadTemplate ('sink',
        gst.PAD_SINK,
        gst.PAD_ALWAYS,
        gst.caps_from_string('application/xspf+xml'))

    srctemplate = gst.PadTemplate ('src',
        gst.PAD_SRC,
        gst.PAD_ALWAYS,
        gst.caps_from_string('text/uri-list'))

    __gsttemplates__ = (sinktemplate, srctemplate)

    def convert(self, data):
        return parse_xspf(data)


class UriListElement(BasePlaylistElement):
    __gstdetails__ = ('URIListDemuxer',
                      'Demuxer',
                      'Convert a text/uri-list to a stream',
                      'Mopidy')

    sinktemplate = gst.PadTemplate ('sink',
        gst.PAD_SINK,
        gst.PAD_ALWAYS,
        gst.caps_from_string('text/uri-list'))

    srctemplate = gst.PadTemplate ('src',
        gst.PAD_SRC,
        gst.PAD_ALWAYS,
        gst.caps_new_any())

    ghostsrc = True  # We need to hook this up to our internal decodebin

    __gsttemplates__ = (sinktemplate, srctemplate)

    def __init__(self):
        super(UriListElement, self).__init__()
        self.uridecodebin = gst.element_factory_make('uridecodebin')
        self.uridecodebin.connect('pad-added', self.pad_added)
        # Limit to anycaps so we get a single stream out, letting other
        # elmenets downstream figure out actual muxing
        self.uridecodebin.set_property('caps', gst.caps_new_any())

    def pad_added(self, src, pad):
        self.src.set_target(pad)

    def handle(self, uris):
        # TODO: hookup about to finish and errors to rest of uris so we
        # round robin, only giving up once all have been tried.
        self.add(self.uridecodebin)
        self.uridecodebin.set_state(gst.STATE_READY)
        self.uridecodebin.set_property('uri', uris[0])
        self.uridecodebin.sync_state_with_parent()
        return True  # Make sure we consume the EOS that triggered us.

    def convert(self, data):
        return parse_urilist(data)


def register_element(element_class):
    gobject.type_register(element_class)
    gst.element_register(
        element_class, element_class.__name__.lower(), gst.RANK_MARGINAL)


def register_elements():
    register_element(M3UDecoder)
    register_element(PLSDecoder)
    register_element(XSPFDecoder)
    register_element(UriListElement)
