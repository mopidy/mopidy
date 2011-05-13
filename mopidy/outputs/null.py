from mopidy.outputs import BaseOutput

class NullOutput(BaseOutput):
    """
    Fall-back null output.

    This output will not output anything. It is intended as a fall-back for
    when setup of all other outputs have failed and should not be used by end
    users. Inserting this output in such a case ensures that the pipeline does
    not crash.
    """

    def describe_bin(self):
        return 'fakesink'


