.. _output-api:

**********
Output API
**********

Outputs are used by :mod:`mopidy.gstreamer` to output audio in some way.

.. autoclass:: mopidy.outputs.BaseOutput
    :members:


Output implementations
======================

* :class:`mopidy.outputs.custom.CustomOutput`
* :class:`mopidy.outputs.local.LocalOutput`
* :class:`mopidy.outputs.shoutcast.ShoutcastOutput`
