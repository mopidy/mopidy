import logging
import optparse
import os
import signal
import sys

import gobject
gobject.threads_init()


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


import mopidy
from mopidy import audio, core, settings, utils
from mopidy.utils import log, path, process
from mopidy.utils.deps import list_deps_optparse_callback
from mopidy.utils.settings import list_settings_optparse_callback


logger = logging.getLogger('mopidy.main')


def main():
    signal.signal(signal.SIGTERM, process.exit_handler)
    loop = gobject.MainLoop()
    options = parse_options()
    try:
        log.setup_logging(options.verbosity_level, options.save_debug_log)
        check_old_folders()
        setup_settings(options.interactive)
        audio_ref = setup_audio()
        backend_ref = setup_backend(audio_ref)
        core_ref = setup_core(audio_ref, backend_ref)
        setup_frontends(core_ref)
        loop.run()
    except mopidy.SettingsError as ex:
        logger.error(ex.message)
    except KeyboardInterrupt:
        logger.info(u'Interrupted. Exiting...')
    except Exception as ex:
        logger.exception(ex)
    finally:
        loop.quit()
        stop_frontends()
        stop_core()
        stop_backend()
        stop_audio()
        process.stop_remaining_actors()


def parse_options():
    parser = optparse.OptionParser(version=u'Mopidy %s' % mopidy.get_version())
    parser.add_option(
        '--help-gst',
        action='store_true', dest='help_gst',
        help='show GStreamer help options')
    parser.add_option(
        '-i', '--interactive',
        action='store_true', dest='interactive',
        help='ask interactively for required settings which are missing')
    parser.add_option(
        '-q', '--quiet',
        action='store_const', const=0, dest='verbosity_level',
        help='less output (warning level)')
    parser.add_option(
        '-v', '--verbose',
        action='count', default=1, dest='verbosity_level',
        help='more output (debug level)')
    parser.add_option(
        '--save-debug-log',
        action='store_true', dest='save_debug_log',
        help='save debug log to "./mopidy.log"')
    parser.add_option(
        '--list-settings',
        action='callback', callback=list_settings_optparse_callback,
        help='list current settings')
    parser.add_option(
        '--list-deps',
        action='callback', callback=list_deps_optparse_callback,
        help='list dependencies and their versions')
    return parser.parse_args(args=mopidy_args)[0]


def check_old_folders():
    old_settings_folder = os.path.expanduser(u'~/.mopidy')

    if not os.path.isdir(old_settings_folder):
        return

    logger.warning(
        u'Old settings folder found at %s, settings.py should be moved '
        u'to %s, any cache data should be deleted. See release notes for '
        u'further instructions.', old_settings_folder, mopidy.SETTINGS_PATH)


def setup_settings(interactive):
    path.get_or_create_folder(mopidy.SETTINGS_PATH)
    path.get_or_create_folder(mopidy.DATA_PATH)
    path.get_or_create_file(mopidy.SETTINGS_FILE)
    try:
        settings.validate(interactive)
    except mopidy.SettingsError as ex:
        logger.error(ex.message)
        sys.exit(1)


def setup_audio():
    return audio.Audio.start().proxy()


def stop_audio():
    process.stop_actors_by_class(audio.Audio)


def setup_backend(audio):
    return utils.get_class(settings.BACKENDS[0]).start(audio=audio).proxy()


def stop_backend():
    process.stop_actors_by_class(utils.get_class(settings.BACKENDS[0]))


def setup_core(audio, backend):
    return core.Core.start(audio=audio, backend=backend).proxy()


def stop_core():
    process.stop_actors_by_class(core.Core)


def setup_frontends(core):
    for frontend_class_name in settings.FRONTENDS:
        try:
            utils.get_class(frontend_class_name).start(core=core)
        except mopidy.OptionalDependencyError as ex:
            logger.info(u'Disabled: %s (%s)', frontend_class_name, ex)


def stop_frontends():
    for frontend_class_name in settings.FRONTENDS:
        try:
            process.stop_actors_by_class(utils.get_class(frontend_class_name))
        except mopidy.OptionalDependencyError:
            pass


if __name__ == '__main__':
    main()
