from __future__ import print_function, unicode_literals

import logging
import os
import time

from mopidy import commands, exceptions
from mopidy.audio import scan
from mopidy.utils import path

from . import translator

logger = logging.getLogger(__name__)


def _get_library(args, config):
    libraries = dict((l.name, l) for l in args.registry['local:library'])
    library_name = config['local']['library']

    if library_name not in libraries:
        logger.warning('Local library %s not found', library_name)
        return 1

    logger.debug('Using %s as the local library', library_name)
    return libraries[library_name](config)


class LocalCommand(commands.Command):
    def __init__(self):
        super(LocalCommand, self).__init__()
        self.add_child('scan', ScanCommand())
        self.add_child('clear', ClearCommand())


class ClearCommand(commands.Command):
    help = 'Clear local media files from the local library.'

    def run(self, args, config):
        library = _get_library(args, config)
        prompt = '\nAre you sure you want to clear the library? [y/N] '

        if raw_input(prompt).lower() != 'y':
            print('Clearing library aborted.')
            return 0

        if library.clear():
            print('Library successfully cleared.')
            return 0

        print('Unable to clear library.')
        return 1


class ScanCommand(commands.Command):
    help = 'Scan local media files and populate the local library.'

    def __init__(self):
        super(ScanCommand, self).__init__()
        self.add_argument('--limit',
                          action='store', type=int, dest='limit', default=None,
                          help='Maxmimum number of tracks to scan')

    def run(self, args, config):
        media_dir = config['local']['media_dir']
        scan_timeout = config['local']['scan_timeout']
        flush_threshold = config['local']['scan_flush_threshold']
        excluded_file_extensions = config['local']['excluded_file_extensions']
        excluded_file_extensions = set(
            file_ext.lower() for file_ext in excluded_file_extensions)

        library = _get_library(args, config)

        uri_path_mapping = {}
        uris_in_library = set()
        uris_to_update = set()
        uris_to_remove = set()

        num_tracks = library.load()
        logger.info('Checking %d tracks from library.', num_tracks)

        for track in library.begin():
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
            library.remove(uri)

        logger.info('Checking %s for unknown tracks.', media_dir)
        for relpath in path.find_files(media_dir):
            uri = translator.path_to_local_track_uri(relpath)
            file_extension = os.path.splitext(relpath)[1]

            if file_extension.lower() in excluded_file_extensions:
                logger.debug('Skipped %s: File extension excluded.', uri)
                continue

            if uri not in uris_in_library:
                uris_to_update.add(uri)
                uri_path_mapping[uri] = os.path.join(media_dir, relpath)

        logger.info('Found %d unknown tracks.', len(uris_to_update))
        logger.info('Scanning...')

        uris_to_update = sorted(uris_to_update)[:args.limit]

        scanner = scan.Scanner(scan_timeout)
        progress = _Progress(flush_threshold, len(uris_to_update))

        for uri in uris_to_update:
            try:
                data = scanner.scan(path.path_to_uri(uri_path_mapping[uri]))
                track = scan.audio_data_to_track(data).copy(uri=uri)
                library.add(track)
                logger.debug('Added %s', track.uri)
            except exceptions.ScannerError as error:
                logger.warning('Failed %s: %s', uri, error)

            if progress.increment():
                progress.log()
                if library.flush():
                    logger.debug('Progress flushed.')

        progress.log()
        library.close()
        logger.info('Done scanning.')
        return 0


class _Progress(object):
    def __init__(self, batch_size, total):
        self.count = 0
        self.batch_size = batch_size
        self.total = total
        self.start = time.time()

    def increment(self):
        self.count += 1
        return self.batch_size and self.count % self.batch_size == 0

    def log(self):
        duration = time.time() - self.start
        if self.count >= self.total or not self.count:
            logger.info('Scanned %d of %d files in %ds.',
                        self.count, self.total, duration)
        else:
            remainder = duration / self.count * (self.total - self.count)
            logger.info('Scanned %d of %d files in %ds, ~%ds left.',
                        self.count, self.total, duration, remainder)
