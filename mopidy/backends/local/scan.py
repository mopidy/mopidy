from __future__ import unicode_literals

import logging
import os
import time

from mopidy import exceptions
from mopidy.audio import scan
from mopidy.backends import base
from mopidy.utils import path

logger = logging.getLogger('mopidy.backends.local.scan')


class ScanSubCommand(base.BaseSubCommandProvider):
    name = b'scan'
    help = b'scan local media files'

    def run(self, args, config, extensions):
        media_dir = config['local']['media_dir']
        scan_timeout = config['local']['scan_timeout']
        excluded_file_extensions = config['local']['excluded_file_extensions']

        updaters = {}
        for e in extensions:
            for updater_class in e.get_library_updaters():
                if updater_class and 'local' in updater_class.uri_schemes:
                    updaters[e.ext_name] = updater_class

        if not updaters:
            logging.error('No usable library updaters found.')
            return 1
        elif len(updaters) > 1:
            logging.error('More than one library updater found. '
                          'Provided by: %s', ', '.join(updaters.keys()))
            return 1

        local_updater = updaters.values()[0](config)

        uris_library = set()
        uris_update = set()
        uris_remove = set()

        logging.info('Checking tracks from library.')
        for track in local_updater.load():
            try:
                # TODO: convert local to file uri / path
                stat = os.stat(path.uri_to_path(track.uri))
                if int(stat.st_mtime) > track.last_modified:
                    uris_update.add(track.uri)
                uris_library.add(track.uri)
            except OSError:
                logging.debug('Missing file %s', track.uri)
                uris_remove.add(track.uri)

        logging.info('Removing %d moved or deleted tracks.', len(uris_remove))
        for uri in uris_remove:
            local_updater.remove(uri)

        logging.info('Checking %s for new or modified tracks.', media_dir)
        for uri in path.find_uris(config['local']['media_dir']):
            file_extension = os.path.splitext(path.uri_to_path(uri))[1]
            if file_extension in excluded_file_extensions:
                logging.debug('Skipped %s: File extension excluded.', uri)
                continue

            if uri not in uris_library:
                uris_update.add(uri)

        logging.info('Found %d new or modified tracks.', len(uris_update))
        logging.info('Scanning new and modified tracks.')

        scanner = scan.Scanner(scan_timeout)
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
        return 0


# TODO: move to utils?
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
