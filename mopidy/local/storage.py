from __future__ import absolute_import, unicode_literals

import logging
import os

from mopidy.utils import encoding, path

logger = logging.getLogger(__name__)


def check_dirs_and_files(config):
    if not os.path.isdir(config['local']['media_dir']):
        logger.warning(
            'Local media dir %s does not exist.' %
            config['local']['media_dir'])

    try:
        path.get_or_create_dir(config['local']['data_dir'])
    except EnvironmentError as error:
        logger.warning(
            'Could not create local data dir: %s',
            encoding.locale_decode(error))
