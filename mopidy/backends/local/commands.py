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

    def run(self, args, config, registry):
        media_dir = config['local']['media_dir']
        scan_timeout = config['local']['scan_timeout']
        excluded_file_extensions = set(
            ext.lower() for ext in config['local']['excluded_file_extensions'])

        # TODO: select updater / library to use by name
        updaters = registry['local:library']
        if not updaters:
            logger.error('No usable library updaters found.')
            return 1
        elif len(updaters) > 1:
            logger.error('More than one library updater found. '
                         'Provided by: %s', ', '.join(updaters))
            return 1
        local_updater = updaters[0](config)

        uri_path_mapping = {}
        uris_in_library = set()
        uris_to_update = set()
        uris_to_remove = set()

        tracks = local_updater.load()
        logger.info('Checking %d tracks from library.', len(tracks))
        for track in tracks:
            uri_path_mapping[track.uri] = translator.local_track_uri_to_path(
                track.uri, media_dir)
            try:
                stat = os.stat(uri_path_mapping[track.uri])
                if int(stat.st_mtime) > track.last_modified:
                    uris_to_update.add(track.uri)
                uris_in_library.add(track.uri)
            except OSError:
                logger.debug('Missing file %s', track.uri)
                uris_to_remove.add(track.uri)

        logger.info('Removing %d missing tracks.', len(uris_to_remove))
        for uri in uris_to_remove:
            local_updater.remove(uri)

        logger.info('Checking %s for unknown tracks.', media_dir)
        for relpath in path.find_files(media_dir):
            file_extension = os.path.splitext(relpath)[1]
            if file_extension.lower() in excluded_file_extensions:
                logger.debug('Skipped %s: File extension excluded.', uri)
                continue

            uri = translator.path_to_local_track_uri(relpath)
            if uri not in uris_in_library:
                uris_to_update.add(uri)
                uri_path_mapping[uri] = os.path.join(media_dir, relpath)

        logger.info('Found %d unknown tracks.', len(uris_to_update))
        logger.info('Scanning...')

        scanner = scan.Scanner(scan_timeout)
        progress = Progress(len(uris_to_update))

        for uri in sorted(uris_to_update):
            try:
                data = scanner.scan(path.path_to_uri(uri_path_mapping[uri]))
                track = scan.audio_data_to_track(data).copy(uri=uri)
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
