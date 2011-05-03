import logging

import pygst
pygst.require('0.10')
import gst

from mopidy import settings

logger = logging.getLogger('mopidy.outputs')


class BaseOutput(object):
    """TODO adamcik"""

    def connect_bin(self, pipeline, element_to_link_to):
        """
        Connect output bin to pipeline and given element.
        """
        description = 'queue ! %s' % self.describe_bin()
        logger.debug('Adding new output to tee: %s', description)

        output = self.parse_bin(description)
        self.modify_bin(output)

        pipeline.add(output)
        output.sync_state_with_parent()
        gst.element_link_many(element_to_link_to, output)

    def parse_bin(self, description):
        return gst.parse_bin_from_description(description, True)

    def modify_bin(self, output):
        """
        Modifies bin before it is installed if needed
        """
        pass

    def describe_bin(self):
        """
        Describe bin to be parsed.

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def set_properties(self, element, properties):
        """
        Set properties on element if they have a value.
        """
        for key, value in properties.items():
            if value:
                element.set_property(key, value)


class LocalOutput(BaseOutput):
    """TODO adamcik"""

    def describe_bin(self):
        if settings.LOCAL_OUTPUT_OVERRIDE:
            return settings.LOCAL_OUTPUT_OVERRIDE
        return 'autoaudiosink'


class NullOutput(BaseOutput):
    """TODO adamcik"""

    def describe_bin(self):
        return 'fakesink'


class ShoutcastOutput(BaseOutput):
    """TODO adamcik"""

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
