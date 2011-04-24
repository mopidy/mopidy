from mopidy import settings
from mopidy.gstreamer import BaseOutput

class LocalAudioOutput(BaseOutput):
    def describe_bin(self):
        return 'autoaudiosink'

class CustomOutput(BaseOutput):
    def describe_bin(self):
        return settings.CUSTOM_OUTPUT

class NullOutput(BaseOutput):
    def describe_bin(self):
        return 'fakesink'

class ShoutcastOutput(BaseOutput):
    def describe_bin(self):
        if settings.SHOUTCAST_OVERRIDE:
            return settings.SHOUTCAST_OVERRIDE

        if not settings.SHOUTCAST_SERVER:
            return None

        description = ['audioconvert ! %s ! shout2send' % settings.SHOUTCAST_ENCODER]
        options = {
            u'ip': settings.SHOUTCAST_SERVER,
            u'mount': settings.SHOUTCAST_MOUNT,
            u'port': settings.SHOUTCAST_PORT,
            u'username': settings.SHOUTCAST_USER,
            u'password': settings.SHOUTCAST_PASSWORD,
        }

        for key, value in sorted(options.items()):
            if value:
                description.append('%s="%s"' % (key, value))

        return u' '.join(description)
