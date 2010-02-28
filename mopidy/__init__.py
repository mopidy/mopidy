from mopidy.exceptions import SettingError
from mopidy import settings as original_settings

def get_version():
    return u'0.1.dev'

def get_mpd_protocol_version():
    return u'0.16.0'

class Settings(object):
    def __getattr__(self, attr):
        if not hasattr(original_settings, attr):
            raise SettingError(u'Setting "%s" is not set.' % attr)
        value = getattr(original_settings, attr)
        if type(value) != bool and not value:
            raise SettingError(u'Setting "%s" is empty.' % attr)
        return value

settings = Settings()
