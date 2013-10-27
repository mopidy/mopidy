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


import pygst
pygst.require('0.10')
import gst
import gst.pbutils

from mopidy import config as config_lib, exceptions, ext
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
    excluded_extensions = config['local']['excluded_file_extensions']

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
        if os.path.splitext(path.uri_to_path(uri))[1] in excluded_extensions:
            logging.debug('Skipped %s: File extension excluded.', uri)
            continue

        if uri not in uris_library:
            uris_update.add(uri)

    logging.info('Found %d new or modified tracks.', len(uris_update))
    logging.info('Scanning new and modified tracks.')

    scanner = Scanner(config['local']['scan_timeout'])
    for uri in uris_update:
        try:
            data = scanner.scan(uri)
            data[b'mtime'] = os.path.getmtime(path.uri_to_path(uri))
            track = translator(data)
            local_updater.add(track)
            logging.debug('Added %s', track.uri)
        except exceptions.ScannerError as error:
            logging.warning('Failed %s: %s', uri, error)

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
    def __init__(self, timeout=1000):
        self.discoverer = gst.pbutils.Discoverer(timeout * 1000000)

    def scan(self, uri):
        try:
            info = self.discoverer.discover_uri(uri)
        except gobject.GError as e:
            # Loosing traceback is non-issue since this is from C code.
            raise exceptions.ScannerError(e)

        data = {}
        audio_streams = info.get_audio_streams()

        if not audio_streams:
            raise exceptions.ScannerError('Did not find any audio streams.')

        for stream in audio_streams:
            taglist = stream.get_tags()
            if not taglist:
                continue
            for key in taglist.keys():
                # XXX: For some crazy reason some wma files spit out lists
                # here, not sure if this is due to better data in headers or
                # wma being stupid. So ugly hack for now :/
                if type(taglist[key]) is list:
                    data[key] = taglist[key][0]
                else:
                    data[key] = taglist[key]

        # Never trust metadata for these fields:
        data[b'uri'] = uri
        data[b'duration'] = info.get_duration() // gst.MSECOND

        if data[b'duration'] < 100:
            raise exceptions.ScannerError(
                'Rejecting file with less than 100ms audio data.')

        return data


if __name__ == '__main__':
    main()
