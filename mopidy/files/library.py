from __future__ import unicode_literals

import logging
import operator
import os
import sys
import urllib2

from mopidy import backend, exceptions, models
from mopidy.audio import scan, utils
from mopidy.internal import path

logger = logging.getLogger(__name__)


class FilesLibraryProvider(backend.LibraryProvider):
    """Library for browsing local files."""
    # TODO: get_images that can pull from metadata and/or .folder.png etc?
    # TODO: handle playlists?

    @property
    def root_directory(self):
        if not self._media_dirs:
            return None
        elif len(self._media_dirs) == 1:
            local_path = self._media_dirs[0]['path']
            uri = path.path_to_uri(local_path)
        else:
            uri = 'file:root'
        return models.Ref.directory(name='Files', uri=uri)

    def __init__(self, backend, config):
        super(FilesLibraryProvider, self).__init__(backend)
        self._media_dirs = list(self._get_media_dirs(config))
        self._follow_symlinks = config['files']['follow_symlinks']
        self._show_dotfiles = config['files']['show_dotfiles']
        self._scanner = scan.Scanner(
            timeout=config['files']['metadata_timeout'])

    def browse(self, uri):
        logger.debug('Browsing files at: %s', uri)
        result = []
        local_path = path.uri_to_path(uri)
        if local_path == 'root':
            return list(self._get_media_dirs_refs())
        for dir_entry in os.listdir(local_path):
            child_path = os.path.join(local_path, dir_entry)
            uri = path.path_to_uri(child_path)
            printable_path = child_path.decode(sys.getfilesystemencoding(),
                                               'ignore')

            if os.path.islink(child_path) and not self._follow_symlinks:
                logger.debug('Ignoring symlink: %s', printable_path)
                continue

            if not self._is_in_basedir(os.path.realpath(child_path)):
                logger.debug('Ignoring symlink to outside base dir: %s',
                             printable_path)
                continue

            if not self._show_dotfiles and dir_entry.startswith(b'.'):
                continue

            if os.path.isdir(child_path):
                result.append(models.Ref.directory(name=dir_entry, uri=uri))
            elif os.path.isfile(child_path):
                if self._is_audiofile(uri):
                    result.append(models.Ref.track(name=dir_entry, uri=uri))
                else:
                    logger.debug('Ignoring non-audiofile: %s', printable_path)

        result.sort(key=operator.attrgetter('name'))
        return result

    def lookup(self, uri):
        logger.debug('looking up uri = %s', uri)
        local_path = path.uri_to_path(uri)
        if not self._is_in_basedir(local_path):
            logger.warn('Ignoring URI outside base dir: %s', local_path)
            return []
        try:
            result = self._scanner.scan(uri)
            track = utils.convert_tags_to_track(result.tags).copy(
                uri=uri, length=result.duration)
        except exceptions.ScannerError as e:
            logger.warning('Problem looking up %s: %s', uri, e)
            track = models.Track(uri=uri)
        if not track.name:
            filename = os.path.basename(local_path)
            name = urllib2.unquote(filename).decode(
                sys.getfilesystemencoding(), 'ignore')
            track = track.copy(name=name)
        return [track]

    def _get_media_dirs(self, config):
        for entry in config['files']['media_dirs']:
            media_dir = {}
            media_dir_split = entry.split('|', 1)
            local_path = path.expand_path(
                media_dir_split[0].encode(sys.getfilesystemencoding()))
            if not local_path:
                logger.warn('Could not expand path %s', media_dir_split[0])
                continue
            elif not os.path.isdir(local_path):
                logger.warn('%s is not a directory', local_path)
                continue
            media_dir['path'] = local_path
            if len(media_dir_split) == 2:
                media_dir['name'] = media_dir_split[1]
            else:
                media_dir['name'] = media_dir_split[0].replace(os.sep, '+')
            yield media_dir

    def _get_media_dirs_refs(self):
        for media_dir in self._media_dirs:
            yield models.Ref.directory(
                name=media_dir['name'],
                uri=path.path_to_uri(media_dir['path']))

    def _is_audiofile(self, uri):
        try:
            result = self._scanner.scan(uri)
            logger.debug('got scan result playable: %s for %s',
                         result.uri, str(result.playable))
            return result.playable
        except exceptions.ScannerError as e:
            logger.warning('Problem scanning %s: %s', uri, e)
            return False

    def _is_in_basedir(self, local_path):
        res = False
        base_dirs = [mdir['path'] for mdir in self._media_dirs]
        for base_dir in base_dirs:
            if path.is_path_inside_base_dir(local_path, base_dir):
                res = True
        if not res:
            logger.warn('%s not inside any base_dir', local_path)
        return res
