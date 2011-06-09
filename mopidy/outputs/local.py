from mopidy.outputs import BaseOutput

class LocalOutput(BaseOutput):
    """
    Basic output to local audio sink.

    This output will normally tell GStreamer to choose whatever it thinks is
    best for your system. In other words this is usually a sane choice.

    **Dependencies:**

    - None

    **Settings:**

    - None
    """

    def describe_bin(self):
        return 'autoaudiosink'
