from mopidy import settings
from mopidy.outputs import BaseOutput

class CustomOutput(BaseOutput):
    """
    Custom output for using alternate setups.

    This output is intended to handle two main cases:

    1. Simple things like switching which sink to use. Say :class:`LocalOutput`
       doesn't work for you and you want to switch to ALSA, simple. Set
       :attr:`mopidy.settings.CUSTOM_OUTPUT` to ``alsasink`` and you are good
       to go. Some possible sinks include:

       - alsasink
       - osssink
       - pulsesink
       - ...and many more

    2. Advanced setups that require complete control of the output bin. For
       these cases setup :attr:`mopidy.settings.CUSTOM_OUTPUT` with a
       :command:`gst-launch` compatible string describing the target setup.

    **Dependencies:**

    - None

    **Settings:**

    - :attr:`mopidy.settings.CUSTOM_OUTPUT`
    """

    def describe_bin(self):
        return settings.CUSTOM_OUTPUT
