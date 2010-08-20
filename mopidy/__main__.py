import logging
import optparse
import os
import sys

sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from mopidy import get_version, settings, SettingsError
from mopidy.core import CoreProcess
from mopidy.utils.log import setup_logging
from mopidy.utils.path import get_or_create_folder
from mopidy.utils.settings import list_settings_optparse_callback

logger = logging.getLogger('mopidy.main')

def main():
    options = parse_options()
    setup_logging(options.verbosity_level, options.dump)

    logger.info('-- Starting Mopidy --')

    get_or_create_folder('~/.mopidy/')
    settings.validate()

    # Explictly call run instead of start, so it runs in this process
    CoreProcess().run()

def parse_options():
    parser = optparse.OptionParser(version='Mopidy %s' % get_version())
    parser.add_option('-q', '--quiet',
        action='store_const', const=0, dest='verbosity_level',
        help='less output (warning level)')
    parser.add_option('-v', '--verbose',
        action='store_const', const=2, dest='verbosity_level',
        help='more output (debug level)')
    parser.add_option('--dump',
        action='store_true', dest='dump',
        help='dump debug log to file')
    parser.add_option('--list-settings',
        action='callback', callback=list_settings_optparse_callback,
        help='list current settings')
    return parser.parse_args()[0]

if __name__ == '__main__':
    main()
