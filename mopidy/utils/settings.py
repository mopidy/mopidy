# Absolute import needed to import ~/.config/mopidy/settings.py and not
# ourselves
from __future__ import absolute_import, unicode_literals

import copy
import getpass
import logging
import os
import pprint
import sys

from mopidy import exceptions
from mopidy.utils import formatting, path

logger = logging.getLogger('mopidy.utils.settings')


class SettingsProxy(object):
    def __init__(self, default_settings_module):
        self.default = self._get_settings_dict_from_module(
            default_settings_module)
        self.local = self._get_local_settings()
        self.runtime = {}

    def _get_local_settings(self):
        if not os.path.isfile(path.SETTINGS_FILE):
            return {}
        sys.path.insert(0, path.SETTINGS_PATH)
        # pylint: disable = F0401
        import settings as local_settings_module
        # pylint: enable = F0401
        return self._get_settings_dict_from_module(local_settings_module)

    def _get_settings_dict_from_module(self, module):
        settings = filter(
            lambda (key, value): self._is_setting(key),
            module.__dict__.iteritems())
        return dict(settings)

    def _is_setting(self, name):
        return name.isupper()

    @property
    def current(self):
        current = copy.copy(self.default)
        current.update(self.local)
        current.update(self.runtime)
        return current

    def __getattr__(self, attr):
        if not self._is_setting(attr):
            return

        current = self.current  # bind locally to avoid copying+updates
        if attr not in current:
            raise exceptions.SettingsError('Setting "%s" is not set.' % attr)

        value = current[attr]
        if isinstance(value, basestring) and len(value) == 0:
            raise exceptions.SettingsError('Setting "%s" is empty.' % attr)
        if not value:
            return value
        if attr.endswith('_PATH') or attr.endswith('_FILE'):
            value = path.expand_path(value)
        return value

    def __setattr__(self, attr, value):
        if self._is_setting(attr):
            self.runtime[attr] = value
        else:
            super(SettingsProxy, self).__setattr__(attr, value)

    def validate(self, interactive):
        if interactive:
            self._read_missing_settings_from_stdin(self.current, self.runtime)
        if self.get_errors():
            logger.error(
                'Settings validation errors: %s',
                formatting.indent(self.get_errors_as_string()))
            raise exceptions.SettingsError('Settings validation failed.')

    def _read_missing_settings_from_stdin(self, current, runtime):
        for setting, value in sorted(current.iteritems()):
            if isinstance(value, basestring) and len(value) == 0:
                runtime[setting] = self._read_from_stdin(setting + ': ')

    def _read_from_stdin(self, prompt):
        if '_PASSWORD' in prompt:
            return (
                getpass.getpass(prompt)
                .decode(sys.stdin.encoding, 'ignore'))
        else:
            sys.stdout.write(prompt)
            return (
                sys.stdin.readline().strip()
                .decode(sys.stdin.encoding, 'ignore'))

    def get_errors(self):
        return validate_settings(self.default, self.local)

    def get_errors_as_string(self):
        lines = []
        for (setting, error) in self.get_errors().iteritems():
            lines.append('%s: %s' % (setting, error))
        return '\n'.join(lines)


def validate_settings(defaults, settings):
    """
    Checks the settings for both errors like misspellings and against a set of
    rules for renamed settings, etc.

    Returns mapping from setting names to associated errors.

    :param defaults: Mopidy's default settings
    :type defaults: dict
    :param settings: the user's local settings
    :type settings: dict
    :rtype: dict
    """
    errors = {}

    changed = {
        'DUMP_LOG_FILENAME': 'DEBUG_LOG_FILENAME',
        'DUMP_LOG_FORMAT': 'DEBUG_LOG_FORMAT',
        'FRONTEND': 'FRONTENDS',
        'GSTREAMER_AUDIO_SINK': 'OUTPUT',
        'LOCAL_MUSIC_FOLDER': 'LOCAL_MUSIC_PATH',
        'LOCAL_OUTPUT_OVERRIDE': 'OUTPUT',
        'LOCAL_PLAYLIST_FOLDER': 'LOCAL_PLAYLIST_PATH',
        'LOCAL_TAG_CACHE': 'LOCAL_TAG_CACHE_FILE',
        'MIXER_ALSA_CONTROL': None,
        'MIXER_EXT_PORT': None,
        'MIXER_EXT_SPEAKERS_A': None,
        'MIXER_EXT_SPEAKERS_B': None,
        'MIXER_MAX_VOLUME': None,
        'SERVER': None,
        'SERVER_HOSTNAME': 'MPD_SERVER_HOSTNAME',
        'SERVER_PORT': 'MPD_SERVER_PORT',
        'SPOTIFY_HIGH_BITRATE': 'SPOTIFY_BITRATE',
        'SPOTIFY_LIB_APPKEY': None,
        'SPOTIFY_LIB_CACHE': 'SPOTIFY_CACHE_PATH',
    }

    list_of_one_or_more = [
        'BACKENDS',
        'FRONTENDS',
    ]

    for setting, value in settings.iteritems():
        if setting in changed:
            if changed[setting] is None:
                errors[setting] = 'Deprecated setting. It may be removed.'
            else:
                errors[setting] = 'Deprecated setting. Use %s.' % (
                    changed[setting],)

        elif setting == 'OUTPUTS':
            errors[setting] = (
                'Deprecated setting, please change to OUTPUT. OUTPUT expects '
                'a GStreamer bin description string for your desired output.')

        elif setting == 'SPOTIFY_BITRATE':
            if value not in (96, 160, 320):
                errors[setting] = (
                    'Unavailable Spotify bitrate. Available bitrates are 96, '
                    '160, and 320.')

        elif setting.startswith('SHOUTCAST_OUTPUT_'):
            errors[setting] = (
                'Deprecated setting, please set the value via the GStreamer '
                'bin in OUTPUT.')

        elif setting in list_of_one_or_more:
            if not value:
                errors[setting] = 'Must contain at least one value.'

        elif setting not in defaults and not setting.startswith('CUSTOM_'):
            errors[setting] = 'Unknown setting.'
            suggestion = did_you_mean(setting, defaults)

            if suggestion:
                errors[setting] += ' Did you mean %s?' % suggestion

    return errors


def list_settings_optparse_callback(*args):
    """
    Prints a list of all settings.

    Called by optparse when Mopidy is run with the :option:`--list-settings`
    option.
    """
    from mopidy import settings
    print format_settings_list(settings)
    sys.exit(0)


def format_settings_list(settings):
    errors = settings.get_errors()
    lines = []
    for (key, value) in sorted(settings.current.iteritems()):
        default_value = settings.default.get(key)
        masked_value = mask_value_if_secret(key, value)
        lines.append('%s: %s' % (
            key, formatting.indent(pprint.pformat(masked_value), places=2)))
        if value != default_value and default_value is not None:
            lines.append(
                '  Default: %s' %
                formatting.indent(pprint.pformat(default_value), places=4))
        if errors.get(key) is not None:
            lines.append('  Error: %s' % errors[key])
    return '\n'.join(lines)


def mask_value_if_secret(key, value):
    if key.endswith('PASSWORD') and value:
        return '********'
    else:
        return value


def did_you_mean(setting, defaults):
    """Suggest most likely setting based on levenshtein."""
    if not defaults:
        return None

    setting = setting.upper()
    candidates = [(levenshtein(setting, d), d) for d in defaults]
    candidates.sort()

    if candidates[0][0] <= 3:
        return candidates[0][1]
    return None


def levenshtein(a, b):
    """Calculates the Levenshtein distance between a and b."""
    n, m = len(a), len(b)
    if n > m:
        return levenshtein(b, a)

    current = xrange(n + 1)
    for i in xrange(1, m + 1):
        previous, current = current, [i] + [0] * n
        for j in xrange(1, n + 1):
            add, delete = previous[j] + 1, current[j - 1] + 1
            change = previous[j - 1]
            if a[j - 1] != b[i - 1]:
                change += 1
            current[j] = min(add, delete, change)
    return current[n]
