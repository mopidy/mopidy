from mopidy import settings
from mopidy.exceptions import ConfigError

def get_version():
    return u'0'

def get_mpd_protocol_version():
    return u'0.15.0'

class Config(object):
    def __getattr__(self, attr):
        if not hasattr(settings, attr):
            raise ConfigError(u'Setting "%s" is not set.' % attr)
        value = getattr(settings, attr)
        if type(value) != bool and not value:
            raise ConfigError(u'Setting "%s" is empty.' % attr)
        if type(value) == unicode:
            value = value.encode('utf-8')
        return value

config = Config()
