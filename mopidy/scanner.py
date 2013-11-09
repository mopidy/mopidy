from __future__ import unicode_literals

import argparse
import logging
import os
import sys
import time

import gobject
gobject.threads_init()

# Extract any command line arguments. This needs to be done before GStreamer is
# imported, so that GStreamer doesn't hijack e.g. ``--help``.
mopidy_args = sys.argv[1:]
sys.argv[1:] = []

from mopidy import config as config_lib, exceptions, ext
from mopidy.audio import scan
from mopidy.backends.local import translator
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

    # TODO: cleanup to consistently use local urls, not a random mix of local
    # and file uris depending on how the data was loaded.
    uris_library = set()
    uris_update = set()
    uris_remove = set()

    logging.info('Checking tracks from library.')
    for track in local_updater.load():
        try:
            uri = translator.local_to_file_uri(track.uri, media_dir)
            stat = os.stat(path.uri_to_path(uri))
            if int(stat.st_mtime) > track.last_modified:
                uris_update.add(uri)
            uris_library.add(uri)
        except OSError:
            logging.debug('Missing file %s', track.uri)
            uris_remove.add(track.uri)

    logging.info('Removing %d missing tracks.', len(uris_remove))
    for uri in uris_remove:
        local_updater.remove(uri)

    logging.info('Checking %s for unknown tracks.', media_dir)
    for uri in path.find_uris(config['local']['media_dir']):
        if os.path.splitext(path.uri_to_path(uri))[1] in excluded_extensions:
            logging.debug('Skipped %s: File extension excluded.', uri)
            continue

        if uri not in uris_library:
            uris_update.add(uri)

    logging.info('Found %d unknown tracks.', len(uris_update))
    logging.info('Scanning...')

    scanner = scan.Scanner(config['local']['scan_timeout'])
    progress = Progress(len(uris_update))

    for uri in sorted(uris_update):
        try:
            data = scanner.scan(uri)
            track = scan.audio_data_to_track(data)
            local_updater.add(track)
            logging.debug('Added %s', track.uri)
        except exceptions.ScannerError as error:
            logging.warning('Failed %s: %s', uri, error)

        progress.increment()

    logging.info('Commiting changes.')
    local_updater.commit()


class Progress(object):
    def __init__(self, total):
        self.count = 0
        self.total = total
        self.start = time.time()

    def increment(self):
        self.count += 1
        if self.count % 1000 == 0 or self.count == self.total:
            duration = time.time() - self.start
            remainder = duration / self.count * (self.total - self.count)
            logging.info('Scanned %d of %d files in %ds, ~%ds left.',
                         self.count, self.total, duration, remainder)


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


if __name__ == '__main__':
    main()
