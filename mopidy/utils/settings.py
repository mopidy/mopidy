# Absolute import needed to import ~/.mopidy/settings.py and not ourselves
from __future__ import absolute_import
from copy import copy
import logging
import os
import sys

from mopidy import SettingsError

class SettingsProxy(object):
    def __init__(self, default_settings_module):
        self.default_settings = self._get_settings_dict_from_module(
            default_settings_module)
        self.local_settings = self._get_local_settings()
        self.raw_settings = copy(self.default_settings)
        self.raw_settings.update(self.local_settings)

    def _get_local_settings(self):
        dotdir = os.path.expanduser(u'~/.mopidy/')
        settings_file = os.path.join(dotdir, u'settings.py')
        if os.path.isfile(settings_file):
            sys.path.insert(0, dotdir)
            import settings as local_settings_module
        return self._get_settings_dict_from_module(local_settings_module)

    def _get_settings_dict_from_module(self, module):
        settings = filter(lambda (key, value): self._is_setting(key),
            module.__dict__.iteritems())
        return dict(settings)

    def _is_setting(self, name):
        return name.isupper()

    def __getattr__(self, attr):
        if not self._is_setting(attr):
            return
        if attr not in self.raw_settings:
            raise SettingsError(u'Setting "%s" is not set.' % attr)
        value = self.raw_settings[attr]
        if type(value) != bool and not value:
            raise SettingsError(u'Setting "%s" is empty.' % attr)
        return value

    def validate(self):
        if self.get_errors():
            sys.exit(self.get_errors_as_string())

    def get_errors(self):
        return validate_settings(self.default_settings, self.local_settings)

    def get_errors_as_string(self):
        lines = [u'Errors:']
        for (setting, error) in self.get_errors().iteritems():
            lines.append(u'  %s: %s' % (setting, error))
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
            break

        if setting == 'BACKENDS':
            if 'mopidy.backends.despotify.DespotifyBackend' in value:
                errors[setting] = (u'Deprecated setting value. ' +
                    '"mopidy.backends.despotify.DespotifyBackend" is no ' +
                    'longer available.')
                break

        if setting not in defaults:
            errors[setting] = u'Unknown setting. Is it misspelled?'
            break

    return errors
