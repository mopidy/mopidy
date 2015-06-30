from __future__ import unicode_literals

import logging
import operator
import os
import stat
import sys
import urllib2


from mopidy import backend, exceptions, models
from mopidy.audio import scan, utils
from mopidy.internal import path

logger = logging.getLogger(__name__)


class FilesLibraryProvider(backend.LibraryProvider):
    """Library for browsing local files."""

    @property
    def root_directory(self):
        if not self._media_dirs:
            return None
        elif len(self._media_dirs) == 1:
            localpath = self._media_dirs[0]['path']
            uri = path.path_to_uri(localpath)
        else:
            uri = u'file:root'
        return models.Ref.directory(name='Files', uri=uri)

    def __init__(self, backend, config):
        super(FilesLibraryProvider, self).__init__(backend)
        self._media_dirs = []
        # import pdb; pdb.set_trace()
        for entry in config['files']['media_dir']:
            media_dir = {}
            media_dict = entry.split(':')
            local_path = path.expand_path(
                media_dict[0].encode(sys.getfilesystemencoding()))
            st = os.stat(local_path)
            if not stat.S_ISDIR(st.st_mode):
                logger.warn(u'%s is not a directory' % local_path)
                continue
            media_dir['path'] = local_path
            if len(media_dict) == 2:
                media_dir['name'] = media_dict[1]
            else:
                media_dir['name'] = media_dict[0].replace(os.sep, '+')
            self._media_dirs.append(media_dir)
        logger.debug(self._media_dirs)
        self._follow_symlinks = config['files']['follow_symlinks']
        self._show_hidden = config['files']['show_hidden']
        self._scanner = scan.Scanner(
            timeout=config['files']['metadata_timeout'])

    def browse(self, uri, encoding=sys.getfilesystemencoding()):
        logger.debug(u'browse called with uri %s' % uri)
        # import pdb; pdb.set_trace()
        result = []
        localpath = path.uri_to_path(uri)
        if localpath == 'root':
            result = self._show_media_dirs()
        else:
            if not self._is_in_basedir(localpath):
                logger.warn(u'Not in basedir: %s' % localpath)
                return []
            for name in os.listdir(localpath):
                child = os.path.join(localpath, name)
                uri = path.path_to_uri(child)
                name = name.decode('ascii', 'ignore')
                if self._follow_symlinks:
                    st = os.stat(child)
                else:
                    st = os.lstat(child)
                if not self._show_hidden and name.startswith(b'.'):
                    continue
                elif stat.S_ISDIR(st.st_mode):
                    result.append(models.Ref.directory(name=name, uri=uri))
                elif stat.S_ISREG(st.st_mode) and self._check_audiofile(uri):
                    # if self._is_playlist(child):
                    #     result.append(models.Ref.playlist(
                    #         name=name,
                    #         uri='m3u:%s' % child))
                    # else:
                    result.append(models.Ref.track(name=name, uri=uri))
                else:
                    logger.warn(u'Ignored file: %s' % child.decode(encoding,
                                                                   'replace'))
                    pass

        result.sort(key=operator.attrgetter('name'))
        return result

    def lookup(self, uri):
        logger.debug(u'looking up uri = %s' % uri)
        localpath = path.uri_to_path(uri)
        if not self._is_in_basedir(localpath):
            logger.warn(u'Not in basedir: %s' % localpath)
            return []
        # import pdb; pdb.set_trace()
        try:
            result = self._scanner.scan(uri)
            track = utils.convert_tags_to_track(result.tags).copy(
                uri=uri, length=result.duration)
        except exceptions.ScannerError as e:
            logger.warning(u'Problem looking up %s: %s', uri, e)
            track = models.Track(uri=uri)
            pass
        if not track.name:
            filename = os.path.basename(localpath)
            name = urllib2.unquote(filename).decode('ascii', 'ignore')
            track = track.copy(name=name)
        return [track]

    # TODO: get_images that can pull from metadata and/or .folder.png etc?

    def _show_media_dirs(self):
        result = []
        for media_dir in self._media_dirs:
            dir = models.Ref.directory(
                name=media_dir['name'],
                uri=path.path_to_uri(media_dir['path']))
            result.append(dir)
        return result

    def _check_audiofile(self, uri):
        try:
            result = self._scanner.scan(uri)
            logger.debug(u'got scan result playable: %s for %s' % (
                result.uri, str(result.playable)))
            res = result.playable
        except exceptions.ScannerError as e:
            logger.warning(u'Problem looking up %s: %s', uri, e)
            res = False
        return res

    def _is_playlist(self, child):
        return os.path.splitext(child)[1] == '.m3u'

    def _is_in_basedir(self, localpath):
        res = False
        basedirs = [mdir['path'] for mdir in self._media_dirs]
        for basedir in basedirs:
            if basedir == localpath:
                res = True
            else:
                try:
                    path.check_file_path_is_inside_base_dir(localpath, basedir)
                    res = True
                except:
                    pass
        if not res:
            logger.warn(u'%s not inside any basedir' % localpath)
        return res
