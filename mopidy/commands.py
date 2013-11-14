from __future__ import unicode_literals

import argparse
import gobject
import logging

from mopidy import config as config_lib
from mopidy.audio import Audio
from mopidy.core import Core
from mopidy.utils import command, deps, process, versioning

logger = logging.getLogger('mopidy.commands')


def config_files_type(value):
    return value.split(b':')


def config_override_type(value):
    try:
        section, remainder = value.split(b'/', 1)
        key, value = remainder.split(b'=', 1)
        return (section.strip(), key.strip(), value.strip())
    except ValueError:
        raise argparse.ArgumentTypeError(
            '%s must have the format section/key=value' % value)


class RootCommand(command.Command):
    def __init__(self):
        super(RootCommand, self).__init__()
        self.set(base_verbosity_level=0)
        self.add_argument(
            '-h', '--help',
            action='help', help='Show this message and exit')
        self.add_argument(
            '--version', action='version',
            version='Mopidy %s' % versioning.get_version())
        self.add_argument(
            '-q', '--quiet',
            action='store_const', const=-1, dest='verbosity_level',
            help='less output (warning level)')
        self.add_argument(
            '-v', '--verbose',
            action='count', dest='verbosity_level', default=0,
            help='more output (debug level)')
        self.add_argument(
            '--save-debug-log',
            action='store_true', dest='save_debug_log',
            help='save debug log to "./mopidy.log"')
        self.add_argument(
            '--config',
            action='store', dest='config_files', type=config_files_type,
            default=b'$XDG_CONFIG_DIR/mopidy/mopidy.conf', metavar='FILES',
            help='config files to use, colon seperated, later files override')
        self.add_argument(
            '-o', '--option',
            action='append', dest='config_overrides',
            type=config_override_type, metavar='OPTIONS',
            help='`section/key=value` values to override config options')

    def run(self, args, config, extensions):
        loop = gobject.MainLoop()
        try:
            audio = self.start_audio(config)
            backends = self.start_backends(config, extensions, audio)
            core = self.start_core(audio, backends)
            self.start_frontends(config, extensions, core)
            loop.run()
        except KeyboardInterrupt:
            logger.info('Interrupted. Exiting...')
            return
        finally:
            loop.quit()
            self.stop_frontends(extensions)
            self.stop_core()
            self.stop_backends(extensions)
            self.stop_audio()
            process.stop_remaining_actors()

    def start_audio(self, config):
        logger.info('Starting Mopidy audio')
        return Audio.start(config=config).proxy()

    def start_backends(self, config, extensions, audio):
        backend_classes = []
        for extension in extensions:
            backend_classes.extend(extension.get_backend_classes())

        logger.info(
            'Starting Mopidy backends: %s',
            ', '.join(b.__name__ for b in backend_classes) or 'none')

        backends = []
        for backend_class in backend_classes:
            backend = backend_class.start(config=config, audio=audio).proxy()
            backends.append(backend)

        return backends

    def start_core(self, audio, backends):
        logger.info('Starting Mopidy core')
        return Core.start(audio=audio, backends=backends).proxy()

    def start_frontends(self, config, extensions, core):
        frontend_classes = []
        for extension in extensions:
            frontend_classes.extend(extension.get_frontend_classes())

        logger.info(
            'Starting Mopidy frontends: %s',
            ', '.join(f.__name__ for f in frontend_classes) or 'none')

        for frontend_class in frontend_classes:
            frontend_class.start(config=config, core=core)

    def stop_frontends(self, extensions):
        logger.info('Stopping Mopidy frontends')
        for extension in extensions:
            for frontend_class in extension.get_frontend_classes():
                process.stop_actors_by_class(frontend_class)

    def stop_core(self):
        logger.info('Stopping Mopidy core')
        process.stop_actors_by_class(Core)

    def stop_backends(self, extensions):
        logger.info('Stopping Mopidy backends')
        for extension in extensions:
            for backend_class in extension.get_backend_classes():
                process.stop_actors_by_class(backend_class)

    def stop_audio(self):
        logger.info('Stopping Mopidy audio')
        process.stop_actors_by_class(Audio)


class ConfigCommand(command.Command):
    """Show currently active configuration."""

    def __init__(self):
        super(ConfigCommand, self).__init__()
        self.set(base_verbosity_level=-1)

    def run(self, config, errors, extensions):
        print config_lib.format(config, extensions, errors)
        return 0


class DepsCommand(command.Command):
    """Show dependencies and debug information."""

    def __init__(self):
        super(DepsCommand, self).__init__()
        self.set(base_verbosity_level=-1)

    def run(self):
        print deps.format_dependency_list()
        return 0
