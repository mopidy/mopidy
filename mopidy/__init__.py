from mopidy import settings as raw_settings

def get_version():
    return u'0.1.0a0'

def get_mpd_protocol_version():
    return u'0.16.0'

class SettingsError(Exception):
    pass

class Settings(object):
    def __getattr__(self, attr):
        if attr.isupper() and not hasattr(raw_settings, attr):
            raise SettingsError(u'Setting "%s" is not set.' % attr)
        value = getattr(raw_settings, attr)
        if type(value) != bool and not value:
            raise SettingsError(u'Setting "%s" is empty.' % attr)
        return value

settings = Settings()
