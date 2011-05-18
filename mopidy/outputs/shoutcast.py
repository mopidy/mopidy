import logging

from mopidy import settings
from mopidy.outputs import BaseOutput

logger = logging.getLogger('mopidy.outputs.shoutcast')

class ShoutcastOutput(BaseOutput):
    """
    Shoutcast streaming output.

    This output allows for streaming to an icecast server or anything else that
    supports Shoutcast. The output supports setting for: server address, port,
    mount point, user, password and encoder to use. Please see
    :class:`mopidy.settings` for details about settings.
    """

    def describe_bin(self):
        return 'audioconvert ! %s ! shout2send name=shoutcast' \
            % settings.SHOUTCAST_OUTPUT_ENCODER

    def modify_bin(self):
        self.set_properties(self.bin.get_by_name('shoutcast'), {
            u'ip': settings.SHOUTCAST_OUTPUT_SERVER,
            u'mount': settings.SHOUTCAST_OUTPUT_MOUNT,
            u'port': settings.SHOUTCAST_OUTPUT_PORT,
            u'username': settings.SHOUTCAST_OUTPUT_USERNAME,
            u'password': settings.SHOUTCAST_OUTPUT_PASSWORD,
        })

    def on_connect(self):
        self.gstreamer.connect_message_handler(
            self.bin.get_by_name('shoutcast'), self.message_handler)

    def on_remove(self):
        self.gstreamer.remove_message_handler(
            self.bin.get_by_name('shoutcast'))

    def message_handler(self, message):
        if message.type != self.MESSAGE_ERROR:
            return False
        error, debug = message.parse_error()
        logger.warning('%s (%s)', error, debug)
        self.remove()
        return True
