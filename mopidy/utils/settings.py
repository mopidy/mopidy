# Absolute import needed to import ~/.mopidy/settings.py and not ourselves
from __future__ import absolute_import
from copy import copy
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

