from mopidy import settings
from mopidy.gstreamer import BaseOutput

class LocalOutput(BaseOutput):
    def describe_bin(self):
        if settings.LOCAL_OUTPUT_OVERRIDE:
            return settings.LOCAL_OUTPUT_OVERRIDE
        return 'autoaudiosink'

class NullOutput(BaseOutput):
    def describe_bin(self):
        return 'fakesink'

class ShoutcastOutput(BaseOutput):
    def describe_bin(self):
        if settings.SHOUTCAST_OUTPUT_OVERRIDE:
            return settings.SHOUTCAST_OUTPUT_OVERRIDE
        return 'audioconvert ! %s ! shout2send name=shoutcast' \
            % settings.SHOUTCAST_OUTPUT_ENCODER

    def modify_bin(self, output):
        if settings.SHOUTCAST_OUTPUT_OVERRIDE:
            return

        self.set_properties(output.get_by_name('shoutcast'), {
            u'ip': settings.SHOUTCAST_OUTPUT_SERVER,
            u'mount': settings.SHOUTCAST_OUTPUT_MOUNT,
            u'port': settings.SHOUTCAST_OUTPUT_PORT,
            u'username': settings.SHOUTCAST_OUTPUT_USERNAME,
            u'password': settings.SHOUTCAST_OUTPUT_PASSWORD,
        })
