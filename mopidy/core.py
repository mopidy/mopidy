import logging
import optparse
import sys
import time

# Extract any non-GStreamer arguments, and leave the GStreamer arguments for
# processing by GStreamer. This needs to be done before GStreamer is imported,
# so that GStreamer doesn't hijack e.g. ``--help``.
# NOTE This naive fix does not support values like ``bar`` in
# ``--gst-foo bar``. Use equals to pass values, like ``--gst-foo=bar``.
def is_gst_arg(arg):
    return arg.startswith('--gst') or arg == '--help-gst'
gstreamer_args = [arg for arg in sys.argv[1:] if is_gst_arg(arg)]
mopidy_args = [arg for arg in sys.argv[1:] if not is_gst_arg(arg)]
sys.argv[1:] = gstreamer_args

from pykka.registry import ActorRegistry

from mopidy import (get_version, settings, OptionalDependencyError,
    SettingsError)
from mopidy.gstreamer import GStreamer
from mopidy.utils import get_class
from mopidy.utils.log import setup_logging
from mopidy.utils.path import get_or_create_folder, get_or_create_file
from mopidy.utils.process import GObjectEventThread
from mopidy.utils.settings import list_settings_optparse_callback

logger = logging.getLogger('mopidy.core')

def main():
    try:
        options = parse_options()
        setup_logging(options.verbosity_level, options.save_debug_log)
        setup_settings(options.interactive)
        setup_gobject_loop()
        setup_gstreamer()
        setup_mixer()
        setup_backend()
        setup_frontends()
        while ActorRegistry.get_all():
            time.sleep(1)
        logger.info(u'No actors left. Exiting...')
    except KeyboardInterrupt:
        logger.info(u'User interrupt. Exiting...')
        ActorRegistry.stop_all()

def parse_options():
    parser = optparse.OptionParser(version=u'Mopidy %s' % get_version())
    parser.add_option('--help-gst',
        action='store_true', dest='help_gst',
        help='show GStreamer help options')
    parser.add_option('-i', '--interactive',
        action='store_true', dest='interactive',
        help='ask interactively for required settings which is missing')
    parser.add_option('-q', '--quiet',
        action='store_const', const=0, dest='verbosity_level',
        help='less output (warning level)')
    parser.add_option('-v', '--verbose',
        action='store_const', const=2, dest='verbosity_level',
        help='more output (debug level)')
    parser.add_option('--save-debug-log',
        action='store_true', dest='save_debug_log',
        help='save debug log to "./mopidy.log"')
    parser.add_option('--list-settings',
        action='callback', callback=list_settings_optparse_callback,
        help='list current settings')
    return parser.parse_args(args=mopidy_args)[0]

def setup_settings(interactive):
    get_or_create_folder('~/.mopidy/')
    get_or_create_file('~/.mopidy/settings.py')
    try:
        settings.validate(interactive)
    except SettingsError, e:
        logger.error(e.message)
        sys.exit(1)

def setup_gobject_loop():
    GObjectEventThread().start()

def setup_gstreamer():
    GStreamer.start()

def setup_mixer():
    get_class(settings.MIXER).start()

def setup_backend():
    get_class(settings.BACKENDS[0]).start()

def setup_frontends():
    for frontend_class_name in settings.FRONTENDS:
        try:
            get_class(frontend_class_name).start()
        except OptionalDependencyError as e:
            logger.info(u'Disabled: %s (%s)', frontend_class_name, e)
