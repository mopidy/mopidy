import pygst
pygst.require('0.10')
import gst

import logging

logger = logging.getLogger('mopidy.outputs')

class BaseOutput(object):
    """Base class for pluggable audio outputs."""

    MESSAGE_EOS = gst.MESSAGE_EOS
    MESSAGE_ERROR = gst.MESSAGE_ERROR
    MESSAGE_WARNING = gst.MESSAGE_WARNING

    def __init__(self, gstreamer):
        self.gstreamer = gstreamer
        self.bin = self._build_bin()
        self.bin.set_name(self.get_name())

        self.modify_bin()

    def _build_bin(self):
        description = 'queue ! %s' % self.describe_bin()
        logger.debug('Creating new output: %s', description)
        return gst.parse_bin_from_description(description, True)

    def connect(self):
        """Attach output to GStreamer pipeline."""
        self.gstreamer.connect_output(self.bin)
        self.on_connect()

    def on_connect(self):
        """
        Called after output has been connected to GStreamer pipeline.

        *MAY be implemented by subclass.*
        """
        pass

    def remove(self):
        """Remove output from GStreamer pipeline."""
        self.gstreamer.remove_output(self.bin)
        self.on_remove()

    def on_remove(self):
        """
        Called after output has been removed from GStreamer pipeline.

        *MAY be implemented by subclass.*
        """
        pass

    def get_name(self):
        """
        Get name of the output. Defaults to the output's class name.

        *MAY be implemented by subclass.*

        :rtype: string
        """
        return self.__class__.__name__

    def modify_bin(self):
        """
        Modifies ``self.bin`` before it is installed if needed.

        Overriding this method allows for outputs to modify the constructed bin
        before it is installed. This can for instance be a good place to call
        `set_properties` on elements that need to be configured.

        *MAY be implemented by subclass.*
        """
        pass

    def describe_bin(self):
        """
        Return string describing the output bin in :command:`gst-launch`
        format.

        For simple cases this can just be a sink such as ``autoaudiosink``,
        or it can be a chain like ``element1 ! element2 ! sink``. See the
        manpage of :command:`gst-launch` for details on the format.

        *MUST be implemented by subclass.*

        :rtype: string
        """
        raise NotImplementedError

    def set_properties(self, element, properties):
        """
        Helper method for setting of properties on elements.

        Will call :meth:`gst.Element.set_property` on ``element`` for each key
        in ``properties`` that has a value that is not :class:`None`.

        :param element: element to set properties on
        :type element: :class:`gst.Element`
        :param properties: properties to set on element
        :type properties: dict
        """
        for key, value in properties.items():
            if value is not None:
                element.set_property(key, value)
