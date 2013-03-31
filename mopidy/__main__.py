from __future__ import unicode_literals

import logging
import optparse
import os
import signal
import sys

import gobject
gobject.threads_init()

import pykka.debug


# Extract any non-GStreamer arguments, and leave the GStreamer arguments for
# processing by GStreamer. This needs to be done before GStreamer is imported,
# so that GStreamer doesn't hijack e.g. ``--help``.
# NOTE This naive fix does not support values like ``bar`` in
# ``--gst-foo bar``. Use equals to pass values, like ``--gst-foo=bar``.

def is_gst_arg(argument):
    return argument.startswith('--gst') or argument == '--help-gst'

gstreamer_args = [arg for arg in sys.argv[1:] if is_gst_arg(arg)]
mopidy_args = [arg for arg in sys.argv[1:] if not is_gst_arg(arg)]
sys.argv[1:] = gstreamer_args


# Add ../ to the path so we can run Mopidy from a Git checkout without
# installing it on the system.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


from mopidy import exceptions, settings
from mopidy.audio import Audio
from mopidy.core import Core
from mopidy.utils import (
    deps, importing, log, path, process, settings as settings_utils,
    versioning)


logger = logging.getLogger('mopidy.main')


def main():
    signal.signal(signal.SIGTERM, process.exit_handler)
    signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    loop = gobject.MainLoop()
    options = parse_options()

    try:
        log.setup_logging(options.verbosity_level, options.save_debug_log)
        check_old_folders()
        setup_settings(options.interactive)
        audio = setup_audio()
        backends = setup_backends(audio)
        core = setup_core(audio, backends)
        setup_frontends(core)
        loop.run()
    except exceptions.SettingsError as ex:
        logger.error(ex.message)
    except KeyboardInterrupt:
        logger.info('Interrupted. Exiting...')
    except Exception as ex:
        logger.exception(ex)
    finally:
        loop.quit()
        stop_frontends()
        stop_core()
        stop_backends()
        stop_audio()
        process.stop_remaining_actors()


def parse_options():
    parser = optparse.OptionParser(
        version='Mopidy %s' % versioning.get_version())
    # NOTE First argument to add_option must be bytestrings on Python < 2.6.2
    # See https://github.com/mopidy/mopidy/issues/302 for details
    parser.add_option(
        b'--help-gst',
        action='store_true', dest='help_gst',
        help='show GStreamer help options')
    parser.add_option(
        b'-i', '--interactive',
        action='store_true', dest='interactive',
        help='ask interactively for required settings which are missing')
    parser.add_option(
        b'-q', '--quiet',
        action='store_const', const=0, dest='verbosity_level',
        help='less output (warning level)')
    parser.add_option(
        b'-v', '--verbose',
        action='count', default=1, dest='verbosity_level',
        help='more output (debug level)')
    parser.add_option(
        b'--save-debug-log',
        action='store_true', dest='save_debug_log',
        help='save debug log to "./mopidy.log"')
    parser.add_option(
        b'--list-settings',
        action='callback',
        callback=settings_utils.list_settings_optparse_callback,
        help='list current settings')
    parser.add_option(
        b'--list-deps',
        action='callback', callback=deps.list_deps_optparse_callback,
        help='list dependencies and their versions')
    parser.add_option(
        b'--debug-thread',
        action='store_true', dest='debug_thread',
        help='run background thread that dumps tracebacks on SIGUSR1')
    return parser.parse_args(args=mopidy_args)[0]


def check_old_folders():
    old_settings_folder = os.path.expanduser('~/.mopidy')

    if not os.path.isdir(old_settings_folder):
        return

    logger.warning(
        'Old settings folder found at %s, settings.py should be moved '
        'to %s, any cache data should be deleted. See release notes for '
        'further instructions.', old_settings_folder, path.SETTINGS_PATH)


def setup_settings(interactive):
    path.get_or_create_folder(path.SETTINGS_PATH)
    path.get_or_create_folder(path.DATA_PATH)
    path.get_or_create_file(path.SETTINGS_FILE)
    try:
        settings.validate(interactive)
    except exceptions.SettingsError as ex:
        logger.error(ex.message)
        sys.exit(1)


def setup_audio():
    return Audio.start().proxy()


def stop_audio():
    process.stop_actors_by_class(Audio)


def setup_backends(audio):
    backends = []
    for backend_class_name in settings.BACKENDS:
        backend_class = importing.get_class(backend_class_name)
        backend = backend_class.start(audio=audio).proxy()
        backends.append(backend)
    return backends


def stop_backends():
    for backend_class_name in settings.BACKENDS:
        process.stop_actors_by_class(importing.get_class(backend_class_name))


def setup_core(audio, backends):
    return Core.start(audio=audio, backends=backends).proxy()


def stop_core():
    process.stop_actors_by_class(Core)


def setup_frontends(core):
    for frontend_class_name in settings.FRONTENDS:
        try:
            importing.get_class(frontend_class_name).start(core=core)
        except exceptions.OptionalDependencyError as ex:
            logger.info('Disabled: %s (%s)', frontend_class_name, ex)


def stop_frontends():
    for frontend_class_name in settings.FRONTENDS:
        try:
            frontend_class = importing.get_class(frontend_class_name)
            process.stop_actors_by_class(frontend_class)
        except exceptions.OptionalDependencyError:
            pass


if __name__ == '__main__':
    main()
