**********
Output API
**********

Outputs are used by :mod:`mopidy.gstreamer` to output audio in some way.

.. autoclass:: mopidy.outputs.BaseOutput
    :members:


Output implementations
======================

* :class:`mopidy.outputs.LocalOutput`
* :class:`mopidy.outputs.NullOutput`
* :class:`mopidy.outputs.ShoutcastOutput`
