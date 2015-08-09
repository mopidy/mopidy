.. _audio-api:

*********************************
:mod:`mopidy.audio` --- Audio API
*********************************

.. module:: mopidy.audio
    :synopsis: Thin wrapper around the parts of GStreamer we use


The audio API is the interface we have built around GStreamer to support our
specific use cases. Most backends should be able to get by with simply setting
the URI of the resource they want to play, for these cases the default playback
provider should be used.

For more advanced cases such as when the raw audio data is delivered outside of
GStreamer or the backend needs to add metadata to the currently playing
resource, developers should sub-class the base playback provider and implement
the extra behaviour that is needed through the following API:


.. autoclass:: mopidy.audio.Audio
    :members:


Audio listener
==============

.. autoclass:: mopidy.audio.AudioListener
    :members:


Audio scanner
=============

.. autoclass:: mopidy.audio.scan.Scanner
    :members:

Audio utils
===========

.. automodule:: mopidy.audio.utils
    :members:
