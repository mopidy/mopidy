from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst
import gobject

import ConfigParser as configparser
import io

try:
    import xml.etree.cElementTree as elementtree
except ImportError:
    import xml.etree.ElementTree as elementtree


# TODO: make detect_FOO_header reusable in general mopidy code.
# i.e. give it just a "peek" like function.
def detect_m3u_header(typefind):
    return typefind.peek(0, 8) == b'#EXTM3U\n'


def detect_pls_header(typefind):
    return typefind.peek(0, 11).lower() == b'[playlist]\n'


def detect_xspf_header(typefind):
    data = typefind.peek(0, 150)
    if b'xspf' not in data:
        return False

    try:
        data = io.BytesIO(data)
        for event, element in elementtree.iterparse(data, events=(b'start',)):
            return element.tag.lower() == '{http://xspf.org/ns/0/}playlist'
    except elementtree.ParseError:
        pass
    return False


def detect_asx_header(typefind):
    data = typefind.peek(0, 50)
    if b'asx' not in data:
        return False

    try:
        data = io.BytesIO(data)
        for event, element in elementtree.iterparse(data, events=(b'start',)):
            return element.tag.lower() == 'asx'
    except elementtree.ParseError:
        pass
    return False


def parse_m3u(data):
    # TODO: convert non URIs to file URIs.
    found_header = False
    for line in data.readlines():
        if found_header or line.startswith('#EXTM3U'):
            found_header = True
        else:
            continue
        if not line.startswith('#') and line.strip():
            yield line.strip()


def parse_pls(data):
    # TODO: convert non URIs to file URIs.
    try:
        cp = configparser.RawConfigParser()
        cp.readfp(data)
    except configparser.Error:
        return

    for section in cp.sections():
        if section.lower() != 'playlist':
            continue
        for i in xrange(cp.getint(section, 'numberofentries')):
            yield cp.get(section, 'file%d' % (i+1))


def parse_xspf(data):
    try:
        for event, element in elementtree.iterparse(data):
            element.tag = element.tag.lower()  # normalize
    except elementtree.ParseError:
        return

    ns = 'http://xspf.org/ns/0/'
    for track in element.iterfind('{%s}tracklist/{%s}track' % (ns, ns)):
        yield track.findtext('{%s}location' % ns)


def parse_asx(data):
    try:
        for event, element in elementtree.iterparse(data):
            element.tag = element.tag.lower()  # normalize
    except elementtree.ParseError:
        return

    for ref in element.findall('entry/ref'):
        yield ref.get('href', '').strip()


def parse_urilist(data):
    for line in data.readlines():
        if not line.startswith('#') and gst.uri_is_valid(line.strip()):
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
    # NOTE: seems we can't use video/x-ms-asf which is the correct mime for asx
    # as it is shared with asf for streaming videos :/
    register_typefind('audio/x-ms-asx', detect_asx_header, [b'asx'])


class BasePlaylistElement(gst.Bin):
    """Base class for creating GStreamer elements for playlist support.

    This element performs the following steps:

    1. Initializes src and sink pads for the element.
    2. Collects data from the sink until EOS is reached.
    3. Passes the collected data to :meth:`convert` to get a list of URIs.
    4. Passes the list of URIs to :meth:`handle`, default handling is to pass
       the URIs to the src element as a uri-list.
    5. If handle returned true, the EOS consumed and nothing more happens, if
       it is not consumed it flows on to the next element downstream, which is
       likely our uri-list consumer which needs the EOS to know we are done
       sending URIs.
    """

    sinkpad_template = None
    """GStreamer pad template to use for sink, must be overriden."""

    srcpad_template = None
    """GStreamer pad template to use for src, must be overriden."""

    ghost_srcpad = False
    """Indicates if src pad should be ghosted or not."""

    def __init__(self):
        """Sets up src and sink pads plus behaviour."""
        super(BasePlaylistElement, self).__init__()
        self._data = io.BytesIO()
        self._done = False

        self.sinkpad = gst.Pad(self.sinkpad_template)
        self.sinkpad.set_chain_function(self._chain)
        self.sinkpad.set_event_function(self._event)
        self.add_pad(self.sinkpad)

        if self.ghost_srcpad:
            self.srcpad = gst.ghost_pad_new_notarget('src', gst.PAD_SRC)
        else:
            self.srcpad = gst.Pad(self.srcpad_template)
        self.add_pad(self.srcpad)

    def convert(self, data):
        """Convert the data we have colleted to URIs.

        :param data: collected data buffer
        :type data: :class:`io.BytesIO`
        :returns: iterable or generator of URIs
        """
        raise NotImplementedError

    def handle(self, uris):
        """Do something useful with the URIs.

        :param uris: list of URIs
        :type uris: :type:`list`
        :returns: boolean indicating if EOS should be consumed
        """
        # TODO: handle unicode uris which we can get out of elementtree
        self.srcpad.push(gst.Buffer('\n'.join(uris)))
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

        # Ensure we handle remaining events in a sane way.
        return pad.event_default(event)


class M3uDecoder(BasePlaylistElement):
    __gstdetails__ = ('M3U Decoder',
                      'Decoder',
                      'Convert .m3u to text/uri-list',
                      'Mopidy')

    sinkpad_template = gst.PadTemplate(
        'sink', gst.PAD_SINK, gst.PAD_ALWAYS,
        gst.caps_from_string('audio/x-mpegurl'))

    srcpad_template = gst.PadTemplate(
        'src', gst.PAD_SRC, gst.PAD_ALWAYS,
        gst.caps_from_string('text/uri-list'))

    __gsttemplates__ = (sinkpad_template, srcpad_template)

    def convert(self, data):
        return parse_m3u(data)


class PlsDecoder(BasePlaylistElement):
    __gstdetails__ = ('PLS Decoder',
                      'Decoder',
                      'Convert .pls to text/uri-list',
                      'Mopidy')

    sinkpad_template = gst.PadTemplate(
        'sink', gst.PAD_SINK, gst.PAD_ALWAYS,
        gst.caps_from_string('audio/x-scpls'))

    srcpad_template = gst.PadTemplate(
        'src', gst.PAD_SRC, gst.PAD_ALWAYS,
        gst.caps_from_string('text/uri-list'))

    __gsttemplates__ = (sinkpad_template, srcpad_template)

    def convert(self, data):
        return parse_pls(data)


class XspfDecoder(BasePlaylistElement):
    __gstdetails__ = ('XSPF Decoder',
                      'Decoder',
                      'Convert .pls to text/uri-list',
                      'Mopidy')

    sinkpad_template = gst.PadTemplate(
        'sink', gst.PAD_SINK, gst.PAD_ALWAYS,
        gst.caps_from_string('application/xspf+xml'))

    srcpad_template = gst.PadTemplate(
        'src', gst.PAD_SRC, gst.PAD_ALWAYS,
        gst.caps_from_string('text/uri-list'))

    __gsttemplates__ = (sinkpad_template, srcpad_template)

    def convert(self, data):
        return parse_xspf(data)


class AsxDecoder(BasePlaylistElement):
    __gstdetails__ = ('ASX Decoder',
                      'Decoder',
                      'Convert .asx to text/uri-list',
                      'Mopidy')

    sinkpad_template = gst.PadTemplate(
        'sink', gst.PAD_SINK, gst.PAD_ALWAYS,
        gst.caps_from_string('audio/x-ms-asx'))

    srcpad_template = gst.PadTemplate(
        'src', gst.PAD_SRC, gst.PAD_ALWAYS,
        gst.caps_from_string('text/uri-list'))

    __gsttemplates__ = (sinkpad_template, srcpad_template)

    def convert(self, data):
        return parse_asx(data)


class UriListElement(BasePlaylistElement):
    __gstdetails__ = ('URIListDemuxer',
                      'Demuxer',
                      'Convert a text/uri-list to a stream',
                      'Mopidy')

    sinkpad_template = gst.PadTemplate(
        'sink', gst.PAD_SINK, gst.PAD_ALWAYS,
        gst.caps_from_string('text/uri-list'))

    srcpad_template = gst.PadTemplate(
        'src', gst.PAD_SRC, gst.PAD_ALWAYS,
        gst.caps_new_any())

    ghost_srcpad = True  # We need to hook this up to our internal decodebin

    __gsttemplates__ = (sinkpad_template, srcpad_template)

    def __init__(self):
        super(UriListElement, self).__init__()
        self.uridecodebin = gst.element_factory_make('uridecodebin')
        self.uridecodebin.connect('pad-added', self.pad_added)
        # Limit to anycaps so we get a single stream out, letting other
        # elements downstream figure out actual muxing
        self.uridecodebin.set_property('caps', gst.caps_new_any())

    def pad_added(self, src, pad):
        self.srcpad.set_target(pad)
        pad.add_event_probe(self.pad_event)

    def pad_event(self, pad, event):
        if event.has_name('urilist-played'):
            error = gst.GError(gst.RESOURCE_ERROR, gst.RESOURCE_ERROR_FAILED,
                               b'Nested playlists not supported.')
            message = b'Playlists pointing to other playlists is not supported'
            self.post_message(gst.message_new_error(self, error, message))
        return 1  # GST_PAD_PROBE_OK

    def handle(self, uris):
        struct = gst.Structure('urilist-played')
        event = gst.event_new_custom(gst.EVENT_CUSTOM_UPSTREAM, struct)
        self.sinkpad.push_event(event)

        # TODO: hookup about to finish and errors to rest of URIs so we
        # round robin, only giving up once all have been tried.
        # TODO: uris could be empty.
        self.add(self.uridecodebin)
        self.uridecodebin.set_state(gst.STATE_READY)
        self.uridecodebin.set_property('uri', uris[0])
        self.uridecodebin.sync_state_with_parent()
        return True  # Make sure we consume the EOS that triggered us.

    def convert(self, data):
        return parse_urilist(data)


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


def register_element(element_class):
    gobject.type_register(element_class)
    gst.element_register(
        element_class, element_class.__name__.lower(), gst.RANK_MARGINAL)


def register_elements():
    register_element(M3uDecoder)
    register_element(PlsDecoder)
    register_element(XspfDecoder)
    register_element(AsxDecoder)
    register_element(UriListElement)

    # Only register icy if gst install can't handle it on it's own.
    if not gst.element_make_from_uri(gst.URI_SRC, 'icy://'):
        register_element(IcySrc)
