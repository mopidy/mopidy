from __future__ import absolute_import, unicode_literals

import collections
import logging
import os

import pkg_resources

from mopidy import config as config_lib, exceptions
from mopidy.internal import path


logger = logging.getLogger(__name__)


_extension_data_fields = ['extension', 'entry_point', 'config_schema',
                          'config_defaults', 'command']

ExtensionData = collections.namedtuple('ExtensionData', _extension_data_fields)


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

        :returns: :class:`~mopidy.config.schemas.ConfigSchema`
        """
        schema = config_lib.ConfigSchema(self.ext_name)
        schema['enabled'] = config_lib.Boolean()
        return schema

    @classmethod
    def get_cache_dir(cls, config):
        """Get or create cache directory for the extension.

        Use this directory to cache data that can safely be thrown away.

        :param config: the Mopidy config object
        :return: string
        """
        assert cls.ext_name is not None
        cache_dir_path = bytes(os.path.join(config['core']['cache_dir'],
                                            cls.ext_name))
        path.get_or_create_dir(cache_dir_path)
        return cache_dir_path

    @classmethod
    def get_config_dir(cls, config):
        """Get or create configuration directory for the extension.

        :param config: the Mopidy config object
        :return: string
        """
        assert cls.ext_name is not None
        config_dir_path = bytes(os.path.join(config['core']['config_dir'],
                                             cls.ext_name))
        path.get_or_create_dir(config_dir_path)
        return config_dir_path

    @classmethod
    def get_data_dir(cls, config):
        """Get or create data directory for the extension.

        Use this directory to store data that should be persistent.

        :param config: the Mopidy config object
        :returns: string
        """
        assert cls.ext_name is not None
        data_dir_path = bytes(os.path.join(config['core']['data_dir'],
                                           cls.ext_name))
        path.get_or_create_dir(data_dir_path)
        return data_dir_path

    def get_command(self):
        """Command to expose to command line users running ``mopidy``.

        :returns:
          Instance of a :class:`~mopidy.commands.Command` class.
        """
        pass

    def validate_environment(self):
        """Checks if the extension can run in the current environment.

        Dependencies described by :file:`setup.py` are checked by Mopidy, so
        you should not check their presence here.

        If a problem is found, raise :exc:`~mopidy.exceptions.ExtensionError`
        with a message explaining the issue.

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
        extension registry.

        :param registry: the extension registry
        :type registry: :class:`Registry`
        """
        raise NotImplementedError


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
        try:
            extension_class = entry_point.load(require=False)
        except Exception as e:
            logger.exception("Failed to load extension %s: %s" % (
                entry_point.name, e))
            continue

        try:
            if not issubclass(extension_class, Extension):
                raise TypeError  # issubclass raises TypeError on non-class
        except TypeError:
            logger.error('Entry point %s did not contain a valid extension'
                         'class: %r', entry_point.name, extension_class)
            continue

        try:
            extension = extension_class()
            config_schema = extension.get_config_schema()
            default_config = extension.get_default_config()
            command = extension.get_command()
        except Exception:
            logger.exception('Setup of extension from entry point %s failed, '
                             'ignoring extension.', entry_point.name)
            continue

        installed_extensions.append(ExtensionData(
            extension, entry_point, config_schema, default_config, command))

        logger.debug(
            'Loaded extension: %s %s', extension.dist_name, extension.version)

    names = (ed.extension.ext_name for ed in installed_extensions)
    logger.debug('Discovered extensions: %s', ', '.join(names))
    return installed_extensions


def validate_extension_data(data):
    """Verify extension's dependencies and environment.

    :param extensions: an extension to check
    :returns: if extension should be run
    """

    logger.debug('Validating extension: %s', data.extension.ext_name)

    if data.extension.ext_name != data.entry_point.name:
        logger.warning(
            'Disabled extension %(ep)s: entry point name (%(ep)s) '
            'does not match extension name (%(ext)s)',
            {'ep': data.entry_point.name, 'ext': data.extension.ext_name})
        return False

    try:
        data.entry_point.require()
    except pkg_resources.DistributionNotFound as ex:
        logger.info(
            'Disabled extension %s: Dependency %s not found',
            data.extension.ext_name, ex)
        return False
    except pkg_resources.VersionConflict as ex:
        if len(ex.args) == 2:
            found, required = ex.args
            logger.info(
                'Disabled extension %s: %s required, but found %s at %s',
                data.extension.ext_name, required, found, found.location)
        else:
            logger.info(
                'Disabled extension %s: %s', data.extension.ext_name, ex)
        return False

    try:
        data.extension.validate_environment()
    except exceptions.ExtensionError as ex:
        logger.info(
            'Disabled extension %s: %s', data.extension.ext_name, ex.message)
        return False
    except Exception:
        logger.exception('Validating extension %s failed with an exception.',
                         data.extension.ext_name)
        return False

    if not data.config_schema:
        logger.error('Extension %s does not have a config schema, disabling.',
                     data.extension.ext_name)
        return False
    elif not isinstance(data.config_schema.get('enabled'), config_lib.Boolean):
        logger.error('Extension %s does not have the required "enabled" config'
                     ' option, disabling.', data.extension.ext_name)
        return False

    for key, value in data.config_schema.items():
        if not isinstance(value, config_lib.ConfigValue):
            logger.error('Extension %s config schema contains an invalid value'
                         ' for the option "%s", disabling.',
                         data.extension.ext_name, key)
            return False

    if not data.config_defaults:
        logger.error('Extension %s does not have a default config, disabling.',
                     data.extension.ext_name)
        return False

    return True
