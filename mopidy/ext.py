from __future__ import unicode_literals

import collections
import logging
import pkg_resources

from mopidy import exceptions
from mopidy import config as config_lib


logger = logging.getLogger(__name__)


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

    def get_command(self):
        """Command to expose to command line users running mopidy.

        :returns:
          Instance of a :class:`~mopidy.commands.Command` class.
        """
        pass

    def validate_environment(self):
        """Checks if the extension can run in the current environment

        For example, this method can be used to check if all dependencies that
        are needed are installed. If a problem is found, raise
        :exc:`~mopidy.exceptions.ExtensionError` with a message explaining the
        issue.

        :raises: :exc:`~mopidy.exceptions.ExtensionError`
        :returns: :class:`None`
        """
        pass

    def setup(self, registry):
        """
        Register the extension's components in the extension :class:`Registry`.

        For example, to register a backend::

            def setup(self, registry):
                from .backend import SoundspotBackend
                registry.add('backend', SoundspotBackend)

        See :class:`Registry` for a list of registry keys with a special
        meaning. Mopidy will instantiate and start any classes registered under
        the ``frontend`` and ``backend`` registry keys.

        This method can also be used for other setup tasks not involving the
        extension registry. For example, to register custom GStreamer
        elements::

            def setup(self, registry):
                from .mixer import SoundspotMixer
                gobject.type_register(SoundspotMixer)
                gst.element_register(
                    SoundspotMixer, 'soundspotmixer', gst.RANK_MARGINAL)

        :param registry: the extension registry
        :type registry: :class:`Registry`
        """
        for backend_class in self.get_backend_classes():
            registry.add('backend', backend_class)

        for frontend_class in self.get_frontend_classes():
            registry.add('frontend', frontend_class)

        self.register_gstreamer_elements()

    def get_frontend_classes(self):
        """List of frontend actor classes

        .. deprecated:: 0.18
            Use :meth:`setup` instead.

        :returns: list of :class:`pykka.Actor` subclasses
        """
        return []

    def get_backend_classes(self):
        """List of backend actor classes

        .. deprecated:: 0.18
            Use :meth:`setup` instead.

        :returns: list of :class:`~mopidy.backend.Backend` subclasses
        """
        return []

    def register_gstreamer_elements(self):
        """Hook for registering custom GStreamer elements.

        .. deprecated:: 0.18
            Use :meth:`setup` instead.

        :returns: :class:`None`
        """
        pass


class Registry(collections.Mapping):
    """Registry of components provided by Mopidy extensions.

    Passed to the :meth:`~Extension.setup` method of all extensions. The
    registry can be used like a dict of string keys and lists.

    Some keys have a special meaning, including, but not limited to:

    - ``backend`` is used for Mopidy backend classes.
    - ``frontend`` is used for Mopidy frontend classes.
    - ``local:library`` is used for Mopidy-Local libraries.

    Extensions can use the registry for allow other to extend the extension
    itself. For example the ``Mopidy-Local`` use the ``local:library`` key to
    allow other extensions to register library providers for ``Mopidy-Local``
    to use. Extensions should namespace custom keys with the extension's
    :attr:`~Extension.ext_name`, e.g. ``local:foo`` or ``http:bar``.
    """

    def __init__(self):
        self._registry = {}

    def add(self, name, cls):
        """Add a component to the registry.

        Multiple classes can be registered to the same name.
        """
        self._registry.setdefault(name, []).append(cls)

    def __getitem__(self, name):
        return self._registry.setdefault(name, [])

    def __iter__(self):
        return iter(self._registry)

    def __len__(self):
        return len(self._registry)


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
    logger.debug('Discovered extensions: %s', ', '.join(names))
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
    except pkg_resources.VersionConflict as ex:
        found, required = ex.args
        logger.info(
            'Disabled extension %s: %s required, but found %s at %s',
            extension.ext_name, required, found, found.location)
        return False

    try:
        extension.validate_environment()
    except exceptions.ExtensionError as ex:
        logger.info(
            'Disabled extension %s: %s', extension.ext_name, ex.message)
        return False

    return True
