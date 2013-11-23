from __future__ import unicode_literals

import logging
import os
import time

from mopidy import commands, exceptions
from mopidy.audio import scan
from mopidy.utils import path

from . import translator

logger = logging.getLogger('mopidy.backends.local.commands')


class LocalCommand(commands.Command):
    def __init__(self):
        super(LocalCommand, self).__init__()
        self.add_child('scan', ScanCommand())


class ScanCommand(commands.Command):
    help = "Scan local media files and populate the local library."

    def run(self, args, config, extensions):
        media_dir = config['local']['media_dir']
        scan_timeout = config['local']['scan_timeout']
        excluded_file_extensions = set(
            ext.lower() for ext in config['local']['excluded_file_extensions'])

        updaters = {}
        for e in extensions:
            for updater_class in e.get_library_updaters():
                if updater_class and 'local' in updater_class.uri_schemes:
                    updaters[e.ext_name] = updater_class

        if not updaters:
            logger.error('No usable library updaters found.')
            return 1
        elif len(updaters) > 1:
            logger.error('More than one library updater found. '
                         'Provided by: %s', ', '.join(updaters.keys()))
            return 1

        local_updater = updaters.values()[0](config)

        # TODO: cleanup to consistently use local urls, not a random mix of
        # local and file uris depending on how the data was loaded.
        uris_library = set()
        uris_update = set()
        uris_remove = set()

        tracks = local_updater.load()
        logger.info('Checking %d tracks from library.', len(tracks))
        for track in tracks:
            try:
                uri = translator.local_to_file_uri(track.uri, media_dir)
                stat = os.stat(path.uri_to_path(uri))
                if int(stat.st_mtime) > track.last_modified:
                    uris_update.add(uri)
                uris_library.add(uri)
            except OSError:
                logger.debug('Missing file %s', track.uri)
                uris_remove.add(track.uri)

        logger.info('Removing %d missing tracks.', len(uris_remove))
        for uri in uris_remove:
            local_updater.remove(uri)

        logger.info('Checking %s for unknown tracks.', media_dir)
        for uri in path.find_uris(media_dir):
            file_extension = os.path.splitext(path.uri_to_path(uri))[1]
            if file_extension.lower() in excluded_file_extensions:
                logger.debug('Skipped %s: File extension excluded.', uri)
                continue

            if uri not in uris_library:
                uris_update.add(uri)

        logger.info('Found %d unknown tracks.', len(uris_update))
        logger.info('Scanning...')

        scanner = scan.Scanner(scan_timeout)
        progress = Progress(len(uris_update))

        for uri in sorted(uris_update):
            try:
                data = scanner.scan(uri)
                track = scan.audio_data_to_track(data)
                local_updater.add(track)
                logger.debug('Added %s', track.uri)
            except exceptions.ScannerError as error:
                logger.warning('Failed %s: %s', uri, error)

            progress.increment()

        logger.info('Commiting changes.')
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
            logger.info('Scanned %d of %d files in %ds, ~%ds left.',
                        self.count, self.total, duration, remainder)
