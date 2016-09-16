from __future__ import absolute_import, unicode_literals

import gzip
import json
import logging
import os
import tempfile

from mopidy import models
from mopidy.internal import encoding

logger = logging.getLogger(__name__)


def load(path):
    """
    Deserialize data from file.

    :param path: full path to import file
    :type path: bytes
    :return: deserialized data
    :rtype: dict
    """
    # Todo: raise an exception in case of error?
    if not os.path.isfile(path):
        logger.info('File does not exist: %s', path)
        return {}
    try:
        with gzip.open(path, 'rb') as fp:
            return json.load(fp, object_hook=models.model_json_decoder)
    except (IOError, ValueError) as error:
        logger.warning(
            'Loading JSON failed: %s',
            encoding.locale_decode(error))
        return {}


def dump(path, data):
    """
    Serialize data to file.

    :param path: full path to export file
    :type path: bytes
    :param data: dictionary containing data to save
    :type data: dict
    """
    directory, basename = os.path.split(path)

    # TODO: cleanup directory/basename.* files.
    tmp = tempfile.NamedTemporaryFile(
        prefix=basename + '.', dir=directory, delete=False)

    try:
        with gzip.GzipFile(fileobj=tmp, mode='wb') as fp:
            json.dump(data, fp, cls=models.ModelJSONEncoder,
                      indent=2, separators=(',', ': '))
        os.rename(tmp.name, path)
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
