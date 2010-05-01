from mopidy import settings as raw_settings

def get_version():
    return u'0.1.0a1'

def get_mpd_protocol_version():
    return u'0.16.0'

class MopidyException(Exception):
    def __init__(self, message, *args, **kwargs):
        super(MopidyException, self).__init__(message, *args, **kwargs)
        self._message = message

    @property
    def message(self):
        """Reimplement message field that was deprecated in Python 2.6"""
        return self._message

    @message.setter
    def message(self, message):
        self._message = message

class SettingsError(MopidyException):
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
