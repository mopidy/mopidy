from __future__ import unicode_literals

import sys

from mopidy import config as config_lib, ext
from mopidy.utils import deps


def show_config(args):
    """Prints the effective config and exits."""
    files = vars(args).get('config', b'').split(b':')
    overrides = vars(args).get('overrides', [])

    extensions = ext.load_extensions()
    config, errors = config_lib.load(files, extensions, overrides)

    # Clear out any config for disabled extensions.
    for extension in extensions:
        if not ext.validate_extension(extension):
            config[extension.ext_name] = {b'enabled': False}
            errors[extension.ext_name] = {
                b'enabled': b'extension disabled its self.'}
        elif not config[extension.ext_name]['enabled']:
            config[extension.ext_name] = {b'enabled': False}
            errors[extension.ext_name] = {
                b'enabled': b'extension disabled by config.'}

    print config_lib.format(config, extensions, errors)
    sys.exit(0)


def show_deps():
    """Prints a list of all dependencies and exits."""
    print deps.format_dependency_list()
    sys.exit(0)
