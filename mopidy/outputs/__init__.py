import logging

import pygst
pygst.require('0.10')
import gst

logger = logging.getLogger('mopidy.outputs')


class BaseOutput(object):
    """Base class for providing support for multiple pluggable outputs."""

    def connect_bin(self, pipeline, element):
        """
        Connect output bin to pipeline and given element.

        In normal cases the element will probably be a `tee`,
        thus allowing us to connect any number of outputs. This
        however is why each bin is forced to have its own `queue`
        after the `tee`.

        :param pipeline: gst.Pipeline to add output to.
        :type pipeline: :class:`gst.Pipeline`
        :param element: gst.Element in pipeline to connect output to.
        :type element: :class:`gst.Element`
        """
        description = 'queue ! %s' % self.describe_bin()
        logger.debug('Adding new output to tee: %s', description)

        output = gst.parse_bin_from_description(description, True)
        self.modify_bin(output)

        pipeline.add(output)
        output.sync_state_with_parent() # Required to add to running pipe
        gst.element_link_many(element, output)

    def modify_bin(self, output):
        """
        Modifies bin before it is installed if needed.

        Overriding this method allows for outputs to modify the constructed bin
        before it is installed. This can for instance be a good place to call
        `set_properties` on elements that need to be configured.

        :param output: gst.Bin to modify in some way.
        :type output: :class:`gst.Bin`
        """
        pass

    def describe_bin(self):
        """
        Return text string describing bin in gst-launch format.

        For simple cases this can just be a plain sink such as `autoaudiosink`
        or it can be a chain `element1 ! element2 ! sink`. See `man
        gst-launch0.10` for details on format.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def set_properties(self, element, properties):
        """
        Helper to allow for simple setting of properties on elements.

        Will call `set_property` on the element for each key that has a value
        that is not None.

        :param element: gst.Element to set properties on.
        :type element: :class:`gst.Element`
        :param properties: Dictionary of properties to set on element.
        :type properties: dict
        """
        for key, value in properties.items():
            if value is not None:
                element.set_property(key, value)
