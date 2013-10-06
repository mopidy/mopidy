from __future__ import unicode_literals

import argparse
import datetime
import logging
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
from mopidy.models import Track, Artist, Album
from mopidy.utils import log, path, versioning


def main():
    args = parse_args()
    # TODO: support config files and overrides (shared from main?)
    config_files = [b'/etc/mopidy/mopidy.conf',
                    b'$XDG_CONFIG_DIR/mopidy/mopidy.conf']
    config_overrides = []

    # TODO: decide if we want to avoid this boilerplate some how.
    # Initial config without extensions to bootstrap logging.
    logging_config, _ = config_lib.load(config_files, [], config_overrides)
    log.setup_root_logger()
    log.setup_console_logging(logging_config, args.verbosity_level)

    extensions = ext.load_extensions()
    config, errors = config_lib.load(
        config_files, extensions, config_overrides)
    log.setup_log_levels(config)

    if not config['local']['media_dir']:
        logging.warning('Config value local/media_dir is not set.')
        return

    if not config['local']['scan_timeout']:
        logging.warning('Config value local/scan_timeout is not set.')
        return

    # TODO: missing config error checking and other default setup code.

    updaters = {}
    for e in extensions:
        for updater_class in e.get_library_updaters():
            if updater_class and 'local' in updater_class.uri_schemes:
                updaters[e.ext_name] = updater_class

    if not updaters:
        logging.error('No usable library updaters found.')
        return
    elif len(updaters) > 1:
        logging.error('More than one library updater found. '
                      'Provided by: %s', ', '.join(updaters.keys()))
        return

    local_updater = updaters.values()[0](config)  # TODO: switch to actor?

    media_dir = config['local']['media_dir']

    uris_library = set()
    uris_update = set()
    uris_remove = set()

    logging.info('Checking tracks from library.')
    for track in local_updater.load():
        try:
            stat = os.stat(path.uri_to_path(track.uri))
            if int(stat.st_mtime) > track.last_modified:
                uris_update.add(track.uri)
            uris_library.add(track.uri)
        except OSError:
            uris_remove.add(track.uri)

    logging.info('Removing %d moved or deleted tracks.', len(uris_remove))
    for uri in uris_remove:
        local_updater.remove(uri)

    logging.info('Checking %s for new or modified tracks.', media_dir)
    for uri in path.find_uris(config['local']['media_dir']):
        if uri not in uris_library:
            uris_update.add(uri)

    logging.info('Found %d new or modified tracks.', len(uris_update))

    def store(data):
        track = translator(data)
        local_updater.add(track)
        logging.debug('Added %s', track.uri)

    def debug(uri, error, debug):
        logging.warning('Failed %s: %s', uri, error)
        logging.debug('Debug info for %s: %s', uri, debug)

    scan_timeout = config['local']['scan_timeout']

    logging.info('Scanning new and modified tracks.')
    # TODO: just pass the library in instead?
    scanner = Scanner(uris_update, store, debug, scan_timeout)
    try:
        scanner.start()
    except KeyboardInterrupt:
        scanner.stop()
        raise

    logging.info('Done scanning; commiting changes.')
    local_updater.commit()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version', action='version',
        version='Mopidy %s' % versioning.get_version())
    parser.add_argument(
        '-q', '--quiet',
        action='store_const', const=0, dest='verbosity_level',
        help='less output (warning level)')
    parser.add_argument(
        '-v', '--verbose',
        action='count', default=1, dest='verbosity_level',
        help='more output (debug level)')
    return parser.parse_args(args=mopidy_args)


# TODO: move into scanner.
def translator(data):
    albumartist_kwargs = {}
    album_kwargs = {}
    artist_kwargs = {}
    track_kwargs = {}

    def _retrieve(source_key, target_key, target):
        if source_key in data:
            target[target_key] = data[source_key]

    _retrieve(gst.TAG_ALBUM, 'name', album_kwargs)
    _retrieve(gst.TAG_TRACK_COUNT, 'num_tracks', album_kwargs)
    _retrieve(gst.TAG_ALBUM_VOLUME_COUNT, 'num_discs', album_kwargs)
    _retrieve(gst.TAG_ARTIST, 'name', artist_kwargs)

    if gst.TAG_DATE in data and data[gst.TAG_DATE]:
        date = data[gst.TAG_DATE]
        try:
            date = datetime.date(date.year, date.month, date.day)
        except ValueError:
            pass  # Ignore invalid dates
        else:
            track_kwargs['date'] = date.isoformat()

    _retrieve(gst.TAG_TITLE, 'name', track_kwargs)
    _retrieve(gst.TAG_TRACK_NUMBER, 'track_no', track_kwargs)
    _retrieve(gst.TAG_ALBUM_VOLUME_NUMBER, 'disc_no', track_kwargs)

    # Following keys don't seem to have TAG_* constant.
    _retrieve('album-artist', 'name', albumartist_kwargs)
    _retrieve('musicbrainz-trackid', 'musicbrainz_id', track_kwargs)
    _retrieve('musicbrainz-artistid', 'musicbrainz_id', artist_kwargs)
    _retrieve('musicbrainz-albumid', 'musicbrainz_id', album_kwargs)
    _retrieve(
        'musicbrainz-albumartistid', 'musicbrainz_id', albumartist_kwargs)

    if albumartist_kwargs:
        album_kwargs['artists'] = [Artist(**albumartist_kwargs)]

    track_kwargs['uri'] = data['uri']
    track_kwargs['last_modified'] = int(data['mtime'])
    track_kwargs['length'] = data[gst.TAG_DURATION]
    track_kwargs['album'] = Album(**album_kwargs)
    track_kwargs['artists'] = [Artist(**artist_kwargs)]

    return Track(**track_kwargs)


class Scanner(object):
    def __init__(
            self, uris, data_callback, error_callback=None, scan_timeout=1000):
        self.data = {}
        self.uris = iter(uris)
        self.data_callback = data_callback
        self.error_callback = error_callback
        self.scan_timeout = scan_timeout
        self.loop = gobject.MainLoop()
        self.timeout_id = None

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

        uri = unicode(self.uribin.get_property('uri'))
        self.data['uri'] = uri
        self.data['mtime'] = os.path.getmtime(path.uri_to_path(uri))
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

    def process_timeout(self):
        if self.error_callback:
            uri = self.uribin.get_property('uri')
            self.error_callback(
                uri, 'Scan timed out after %d ms' % self.scan_timeout, None)
        self.next_uri()
        return False

    def get_duration(self):
        self.pipe.get_state()  # Block until state change is done.
        try:
            return self.pipe.query_duration(
                gst.FORMAT_TIME, None)[0] // gst.MSECOND
        except gst.QueryError:
            return None

    def next_uri(self):
        self.data = {}
        if self.timeout_id:
            gobject.source_remove(self.timeout_id)
            self.timeout_id = None
        try:
            uri = next(self.uris)
        except StopIteration:
            self.stop()
            return False
        self.pipe.set_state(gst.STATE_NULL)
        self.uribin.set_property('uri', uri)
        self.timeout_id = gobject.timeout_add(
            self.scan_timeout, self.process_timeout)
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
