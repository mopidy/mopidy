from __future__ import unicode_literals

import logging
import pkg_resources

from mopidy import exceptions
from mopidy import config as config_lib


logger = logging.getLogger('mopidy.ext')


class Extension(object):
    """Base class for Mopidy extensions"""

    dist_name = None
    ext_name = None
    version = None

    def get_default_config(self):
        """TODO"""
        raise NotImplementedError(
            'Add at least a config section with "enabled = true"')

    def get_config_schema(self):
        """TODO"""
        return config_lib.ExtensionConfigSchema()

    def validate_environment(self):
        """TODO"""
        pass

    def get_frontend_classes(self):
        """TODO"""
        return []

    def get_backend_classes(self):
        """TODO"""
        return []

    def register_gstreamer_elements(self):
        """TODO"""
        pass


def load_extensions():
    extensions = []
    for entry_point in pkg_resources.iter_entry_points('mopidy.ext'):
        logger.debug('Loading entry point: %s', entry_point)

        try:
            extension_class = entry_point.load()
        except pkg_resources.DistributionNotFound as ex:
            logger.info(
                'Disabled extension %s: Dependency %s not found',
                entry_point.name, ex)
            continue

        extension = extension_class()

        logger.debug(
            'Loaded extension: %s %s', extension.dist_name, extension.version)

        if entry_point.name != extension.ext_name:
            logger.warning(
                'Disabled extension %(ep)s: entry point name (%(ep)s) '
                'does not match extension name (%(ext)s)',
                {'ep': entry_point.name, 'ext': extension.ext_name})
            continue

        try:
            extension.validate_environment()
        except exceptions.ExtensionError as ex:
            logger.info(
                'Disabled extension %s: %s', entry_point.name, ex.message)
            continue

        extensions.append(extension)

    names = (e.ext_name for e in extensions)
    logging.debug('Discovered extensions: %s', ', '.join(names))
    return extensions


def filter_enabled_extensions(raw_config, extensions):
    boolean = config_lib.Boolean()
    enabled_extensions = []
    enabled_names = []
    disabled_names = []

    for extension in extensions:
        # TODO: handle key and value errors.
        enabled = raw_config[extension.ext_name]['enabled']
        if boolean.deserialize(enabled):
            enabled_extensions.append(extension)
            enabled_names.append(extension.ext_name)
        else:
            disabled_names.append(extension.ext_name)

    logging.info(
        'Enabled extensions: %s', ', '.join(enabled_names) or 'none')
    logging.info(
        'Disabled extensions: %s', ', '.join(disabled_names) or 'none')
    return enabled_extensions
