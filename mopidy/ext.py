from __future__ import unicode_literals

import logging
import pkg_resources

from mopidy import exceptions
from mopidy import config as config_lib


logger = logging.getLogger('mopidy.ext')


class Extension(object):
    """Base class for Mopidy extensions"""

    dist_name = None
    """The extension's distribution name, as registered on PyPI

    Example: ``Mopidy-Soundspot``
    """

    ext_name = None
    """The extension's short name, as used in setup.py and as config section
    name

    Example: ``soundspot``
    """

    version = None
    """The extension's version

    Should match the :attr:`__version__` attribute on the extension's main
    Python module and the version registered on PyPI.
    """

    def get_default_config(self):
        """The extension's default config as a bytestring

        :returns: bytes or unicode
        """
        raise NotImplementedError(
            'Add at least a config section with "enabled = true"')

    def get_config_schema(self):
        """The extension's config validation schema

        :returns: :class:`~mopidy.config.schema.ExtensionConfigSchema`
        """
        schema = config_lib.ConfigSchema(self.ext_name)
        schema['enabled'] = config_lib.Boolean()
        return schema

    def validate_environment(self):
        """Checks if the extension can run in the current environment

        For example, this method can be used to check if all dependencies that
        are needed are installed.

        :raises: :class:`~mopidy.exceptions.ExtensionError`
        :returns: :class:`None`
        """
        pass

    def get_frontend_classes(self):
        """List of frontend actor classes

        Mopidy will take care of starting the actors.

        :returns: list of :class:`pykka.Actor` subclasses
        """
        return []

    def get_backend_classes(self):
        """List of backend actor classes

        Mopidy will take care of starting the actors.

        :returns: list of :class:`~mopidy.backends.base.Backend` subclasses
        """
        return []

    def get_library_updaters(self):
        """List of library updater classes

        :returns: list of
          :class:`~mopidy.backends.base.BaseLibraryUpdateProvider` subclasses
        """
        return []

    def register_gstreamer_elements(self):
        """Hook for registering custom GStreamer elements

        Register custom GStreamer elements by implementing this method.
        Example::

            def register_gstreamer_elements(self):
                from .mixer import SoundspotMixer
                gobject.type_register(SoundspotMixer)
                gst.element_register(
                    SoundspotMixer, 'soundspotmixer', gst.RANK_MARGINAL)

        :returns: :class:`None`
        """
        pass


def load_extensions():
    """Find all installed extensions.

    :returns: list of installed extensions
    """

    installed_extensions = []

    for entry_point in pkg_resources.iter_entry_points('mopidy.ext'):
        logger.debug('Loading entry point: %s', entry_point)
        extension_class = entry_point.load(require=False)
        extension = extension_class()
        extension.entry_point = entry_point
        installed_extensions.append(extension)
        logger.debug(
            'Loaded extension: %s %s', extension.dist_name, extension.version)

    names = (e.ext_name for e in installed_extensions)
    logging.debug('Discovered extensions: %s', ', '.join(names))
    return installed_extensions


def validate_extension(extension):
    """Verify extension's dependencies and environment.

    :param extensions: an extension to check
    :returns: if extension should be run
    """

    logger.debug('Validating extension: %s', extension.ext_name)

    if extension.ext_name != extension.entry_point.name:
        logger.warning(
            'Disabled extension %(ep)s: entry point name (%(ep)s) '
            'does not match extension name (%(ext)s)',
            {'ep': extension.entry_point.name, 'ext': extension.ext_name})
        return False

    try:
        extension.entry_point.require()
    except pkg_resources.DistributionNotFound as ex:
        logger.info(
            'Disabled extension %s: Dependency %s not found',
            extension.ext_name, ex)
        return False

    try:
        extension.validate_environment()
    except exceptions.ExtensionError as ex:
        logger.info(
            'Disabled extension %s: %s', extension.ext_name, ex.message)
        return False

    return True


def register_gstreamer_elements(enabled_extensions):
    """Registers custom GStreamer elements from extensions.

    :param enabled_extensions: list of enabled extensions
    """

    for extension in enabled_extensions:
        logger.debug(
            'Registering GStreamer elements for: %s', extension.ext_name)
        extension.register_gstreamer_elements()
