from __future__ import unicode_literals

import datetime
import logging
import optparse
import os
import sys

import gobject
gobject.threads_init()


# Extract any command line arguments. This needs to be done before GStreamer is
# imported, so that GStreamer doesn't hijack e.g. ``--help``.
mopidy_args = sys.argv[1:]
sys.argv[1:] = []


# Add ../ to the path so we can run Mopidy from a Git checkout without
# installing it on the system.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


import pygst
pygst.require('0.10')
import gst

from mopidy import config as config_lib, ext
from mopidy.frontends.mpd import translator as mpd_translator
from mopidy.models import Track, Artist, Album
from mopidy.utils import log, path, versioning


def main():
    options = parse_options()
    # TODO: support config files and overrides (shared from main?)
    config_files = [b'/etc/mopidy/mopidy.conf',
                    b'$XDG_CONFIG_DIR/mopidy/mopidy.conf']
    config_overrides = []

    # TODO: decide if we want to avoid this boilerplate some how.
    # Initial config without extensions to bootstrap logging.
    logging_config, _ = config_lib.load(config_files, [], config_overrides)
    log.setup_root_logger()
    log.setup_console_logging(logging_config, options.verbosity_level)

    extensions = ext.load_extensions()
    config, errors = config_lib.load(
        config_files, extensions, config_overrides)
    log.setup_log_levels(config)

    if not config['local']['media_dir']:
        logging.warning('Config value local/media_dir is not set.')
        return

    # TODO: missing error checking and other default setup code.

    tracks = []

    def store(data):
        track = translator(data)
        tracks.append(track)
        logging.debug('Added %s', track.uri)

    def debug(uri, error, debug):
        logging.warning('Failed %s: %s', uri, error)
        logging.debug('Debug info for %s: %s', uri, debug)

    logging.info('Scanning %s', config['local']['media_dir'])

    scanner = Scanner(config['local']['media_dir'], store, debug)
    try:
        scanner.start()
    except KeyboardInterrupt:
        scanner.stop()

    logging.info('Done scanning; writing tag cache...')

    for row in mpd_translator.tracks_to_tag_cache_format(
            tracks, config['local']['media_dir']):
        if len(row) == 1:
            print ('%s' % row).encode('utf-8')
        else:
            print ('%s: %s' % row).encode('utf-8')

    logging.info('Done writing tag cache')


def parse_options():
    parser = optparse.OptionParser(
        version='Mopidy %s' % versioning.get_version())
    # NOTE First argument to add_option must be bytestrings on Python < 2.6.2
    # See https://github.com/mopidy/mopidy/issues/302 for details
    parser.add_option(
        b'-q', '--quiet',
        action='store_const', const=0, dest='verbosity_level',
        help='less output (warning level)')
    parser.add_option(
        b'-v', '--verbose',
        action='count', default=1, dest='verbosity_level',
        help='more output (debug level)')
    return parser.parse_args(args=mopidy_args)[0]


def translator(data):
    albumartist_kwargs = {}
    album_kwargs = {}
    artist_kwargs = {}
    track_kwargs = {}

    # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
    # See https://github.com/mopidy/mopidy/issues/302 for details.

    def _retrieve(source_key, target_key, target):
        if source_key in data:
            target[str(target_key)] = data[source_key]

    _retrieve(gst.TAG_ALBUM, 'name', album_kwargs)
    _retrieve(gst.TAG_TRACK_COUNT, 'num_tracks', album_kwargs)
    _retrieve(gst.TAG_ARTIST, 'name', artist_kwargs)

    if gst.TAG_DATE in data and data[gst.TAG_DATE]:
        date = data[gst.TAG_DATE]
        try:
            date = datetime.date(date.year, date.month, date.day)
        except ValueError:
            pass  # Ignore invalid dates
        else:
            track_kwargs[b'date'] = date.isoformat()

    _retrieve(gst.TAG_TITLE, 'name', track_kwargs)
    _retrieve(gst.TAG_TRACK_NUMBER, 'track_no', track_kwargs)

    # Following keys don't seem to have TAG_* constant.
    _retrieve('album-artist', 'name', albumartist_kwargs)
    _retrieve('musicbrainz-trackid', 'musicbrainz_id', track_kwargs)
    _retrieve('musicbrainz-artistid', 'musicbrainz_id', artist_kwargs)
    _retrieve('musicbrainz-albumid', 'musicbrainz_id', album_kwargs)
    _retrieve(
        'musicbrainz-albumartistid', 'musicbrainz_id', albumartist_kwargs)

    if albumartist_kwargs:
        album_kwargs[b'artists'] = [Artist(**albumartist_kwargs)]

    track_kwargs[b'uri'] = data['uri']
    track_kwargs[b'length'] = data[gst.TAG_DURATION]
    track_kwargs[b'album'] = Album(**album_kwargs)
    track_kwargs[b'artists'] = [Artist(**artist_kwargs)]

    return Track(**track_kwargs)


class Scanner(object):
    def __init__(self, base_dir, data_callback, error_callback=None):
        self.data = {}
        self.files = path.find_files(base_dir)
        self.data_callback = data_callback
        self.error_callback = error_callback
        self.loop = gobject.MainLoop()

        self.fakesink = gst.element_factory_make('fakesink')
        self.fakesink.set_property('signal-handoffs', True)
        self.fakesink.connect('handoff', self.process_handoff)

        self.uribin = gst.element_factory_make('uridecodebin')
        self.uribin.set_property(
            'caps', gst.Caps(b'audio/x-raw-int; audio/x-raw-float'))
        self.uribin.connect('pad-added', self.process_new_pad)

        self.pipe = gst.element_factory_make('pipeline')
        self.pipe.add(self.uribin)
        self.pipe.add(self.fakesink)

        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.process_application)
        bus.connect('message::tag', self.process_tags)
        bus.connect('message::error', self.process_error)

    def process_handoff(self, fakesink, buffer_, pad):
        # When this function is called the first buffer has reached the end of
        # the pipeline, and we can continue with the next track. Since we're
        # in another thread, we send a message back to the main thread using
        # the bus.
        structure = gst.Structure('handoff')
        message = gst.message_new_application(fakesink, structure)
        bus = self.pipe.get_bus()
        bus.post(message)

    def process_new_pad(self, source, pad):
        pad.link(self.fakesink.get_pad('sink'))

    def process_application(self, bus, message):
        if message.src != self.fakesink:
            return

        if message.structure.get_name() != 'handoff':
            return

        self.data['uri'] = unicode(self.uribin.get_property('uri'))
        self.data[gst.TAG_DURATION] = self.get_duration()

        try:
            self.data_callback(self.data)
            self.next_uri()
        except KeyboardInterrupt:
            self.stop()

    def process_tags(self, bus, message):
        taglist = message.parse_tag()

        for key in taglist.keys():
            # XXX: For some crazy reason some wma files spit out lists here,
            # not sure if this is due to better data in headers or wma being
            # stupid. So ugly hack for now :/
            if type(taglist[key]) is list:
                self.data[key] = taglist[key][0]
            else:
                self.data[key] = taglist[key]

    def process_error(self, bus, message):
        if self.error_callback:
            uri = self.uribin.get_property('uri')
            error, debug = message.parse_error()
            self.error_callback(uri, error, debug)
        self.next_uri()

    def get_duration(self):
        self.pipe.get_state()  # Block until state change is done.
        try:
            return self.pipe.query_duration(
                gst.FORMAT_TIME, None)[0] // gst.MSECOND
        except gst.QueryError:
            return None

    def next_uri(self):
        self.data = {}
        try:
            uri = path.path_to_uri(self.files.next())
        except StopIteration:
            self.stop()
            return False
        self.pipe.set_state(gst.STATE_NULL)
        self.uribin.set_property('uri', uri)
        self.pipe.set_state(gst.STATE_PLAYING)
        return True

    def start(self):
        if self.next_uri():
            self.loop.run()

    def stop(self):
        self.pipe.set_state(gst.STATE_NULL)
        self.loop.quit()


if __name__ == '__main__':
    main()
