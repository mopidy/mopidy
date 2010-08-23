# Absolute import needed to import ~/.mopidy/settings.py and not ourselves
from __future__ import absolute_import
from copy import copy
import logging
import os
import sys

from mopidy import SettingsError
from mopidy.utils.log import indent

logger = logging.getLogger('mopidy.utils.settings')

class SettingsProxy(object):
    def __init__(self, default_settings_module):
        self.default = self._get_settings_dict_from_module(
            default_settings_module)
        self.local = self._get_local_settings()
        self.runtime = {}

    def _get_local_settings(self):
        dotdir = os.path.expanduser(u'~/.mopidy/')
        settings_file = os.path.join(dotdir, u'settings.py')
        if not os.path.isfile(settings_file):
            return {}
        sys.path.insert(0, dotdir)
        import settings as local_settings_module
        return self._get_settings_dict_from_module(local_settings_module)

    def _get_settings_dict_from_module(self, module):
        settings = filter(lambda (key, value): self._is_setting(key),
            module.__dict__.iteritems())
        return dict(settings)

    def _is_setting(self, name):
        return name.isupper()

    @property
    def current(self):
        current = copy(self.default)
        current.update(self.local)
        current.update(self.runtime)
        return current

    def __getattr__(self, attr):
        if not self._is_setting(attr):
            return
        if attr not in self.current:
            raise SettingsError(u'Setting "%s" is not set.' % attr)
        value = self.current[attr]
        if type(value) != bool and not value:
            raise SettingsError(u'Setting "%s" is empty.' % attr)
        return value

    def __setattr__(self, attr, value):
        if self._is_setting(attr):
            self.runtime[attr] = value
        else:
            super(SettingsProxy, self).__setattr__(attr, value)

    def validate(self):
        if self.get_errors():
            logger.error(u'Settings validation errors: %s',
                indent(self.get_errors_as_string()))
            raise SettingsError(u'Settings validation failed.')

    def get_errors(self):
        return validate_settings(self.default, self.local)

    def get_errors_as_string(self):
        lines = []
        for (setting, error) in self.get_errors().iteritems():
            lines.append(u'%s: %s' % (setting, error))
        return '\n'.join(lines)


def validate_settings(defaults, settings):
    """
    Checks the settings for both errors like misspellings and against a set of
    rules for renamed settings, etc.

    Returns of setting names with associated errors.

    :param defaults: Mopidy's default settings
    :type defaults: dict
    :param settings: the user's local settings
    :type settings: dict
    :rtype: dict
    """
    errors = {}

    changed = {
        'FRONTEND': 'FRONTENDS',
        'SERVER': None,
        'SERVER_HOSTNAME': 'MPD_SERVER_HOSTNAME',
        'SERVER_PORT': 'MPD_SERVER_PORT',
        'SPOTIFY_LIB_APPKEY': None,
    }

    for setting, value in settings.iteritems():
        if setting in changed:
            if changed[setting] is None:
                errors[setting] = u'Deprecated setting. It may be removed.'
            else:
                errors[setting] = u'Deprecated setting. Use %s.' % (
                    changed[setting],)
            continue

        if setting == 'BACKENDS':
            if 'mopidy.backends.despotify.DespotifyBackend' in value:
                errors[setting] = (u'Deprecated setting value. ' +
                    '"mopidy.backends.despotify.DespotifyBackend" is no ' +
                    'longer available.')
                continue

        if setting not in defaults:
            errors[setting] = u'Unknown setting. Is it misspelled?'
            continue

    return errors

def list_settings_optparse_callback(*args):
    """
    Prints a list of all settings.

    Called by optparse when Mopidy is run with the :option:`--list-settings`
    option.
    """
    from mopidy import settings
    errors = settings.get_errors()
    lines = []
    for (key, value) in sorted(settings.current.iteritems()):
        default_value = settings.default.get(key)
        if key.endswith('PASSWORD'):
            value = u'********'
        lines.append(u'%s:' % key)
        lines.append(u'  Value: %s' % repr(value))
        if value != default_value and default_value is not None:
            lines.append(u'  Default: %s' % repr(default_value))
        if errors.get(key) is not None:
            lines.append(u'  Error: %s' % errors[key])
    print u'Settings: %s' % indent('\n'.join(lines), places=2)
    sys.exit(0)
