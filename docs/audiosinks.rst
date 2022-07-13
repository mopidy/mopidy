.. _audiosinks:

***********
Audio sinks
***********

Mopidy has very few :ref:`audio configurations <audio-config>`, but the ones we
have are very powerful because they let you modify the GStreamer audio pipeline
directly.

If you have successfully installed GStreamer, and then run the
``gst-inspect-1.0`` command, you should see a long listing of installed
plugins, ending in a summary line::

    $ gst-inspect-1.0
    ... long list of installed plugins ...
    Total count: 233 plugins, 1339 features

Next, you should be able to produce a audible tone by running::

    gst-launch-1.0 audiotestsrc ! audioresample ! autoaudiosink

If you cannot hear any sound when running this command, you won't hear any
sound from Mopidy either, as Mopidy by default uses GStreamer's
``autoaudiosink`` to play audio. Thus, make this work before you file a bug
against Mopidy.

If you for some reason want to use some other GStreamer audio sink than
``autoaudiosink``, you can set the :confval:`audio/output` config value to a
partial GStreamer pipeline description describing the GStreamer sink you want
to use.

Example ``mopidy.conf`` for using OSS4:

.. code-block:: ini

    [audio]
    output = oss4sink

Again, this is the equivalent of the following ``gst-launch-1.0`` command, so
make this work first::

    gst-launch-1.0 audiotestsrc ! audioresample ! oss4sink
