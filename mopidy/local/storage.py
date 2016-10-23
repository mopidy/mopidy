from __future__ import absolute_import, unicode_literals

import logging
import os

logger = logging.getLogger(__name__)


def check_dirs_and_files(config):
    if not os.path.isdir(config['local']['media_dir']):
        logger.warning(
            'Local media dir %s does not exist or we lack permissions to the '
            'directory or one of its parents' % config['local']['media_dir'])
