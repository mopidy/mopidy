.. _audio:

*********************
Advanced audio setups
*********************

Custom audio sink
=================

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


Streaming through SHOUTcast/Icecast
===================================

.. warning:: Known issue

   Currently, Mopidy does not handle end-of-track vs end-of-stream signalling
   in GStreamer correctly. This causes the SHOUTcast stream to be disconnected
   at the end of each track, rendering it quite useless. For further details,
   see :issue:`492`. You can also try the workaround_ mentioned below.

If you want to play the audio on another computer than the one running Mopidy,
you can stream the audio from Mopidy through an SHOUTcast or Icecast audio
streaming server. Multiple media players can then be connected to the streaming
server simultaneously. To use the SHOUTcast output, do the following:

#. Install, configure and start the Icecast server. It can be found in the
   ``icecast2`` package in Debian/Ubuntu.

#. Set the :confval:`audio/output` config value to ``lamemp3enc ! shout2send``.
   An Ogg Vorbis encoder could be used instead of the lame MP3 encoder.

#. You might also need to change the ``shout2send`` default settings, run
   ``gst-inspect-1.0 shout2send`` to see the available settings. Most likely
   you want to change ``ip``, ``username``, ``password``, and ``mount``.

   Example for MP3 streaming:

   .. code-block:: ini

       [audio]
       output = lamemp3enc ! shout2send mount=mopidy ip=127.0.0.1 port=8000 password=hackme

   Example for Ogg Vorbis streaming:

   .. code-block:: ini

       [audio]
       output = audioresample ! audioconvert ! vorbisenc ! oggmux ! shout2send mount=mopidy ip=127.0.0.1 port=8000 password=hackme

Other advanced setups are also possible for outputs. Basically, anything you
can use with the ``gst-launch-1.0`` command can be plugged into
:confval:`audio/output`.

.. _workaround:

**Workaround for end-of-track issues - fallback streams**

By using a *fallback stream* playing silence, you can somewhat mitigate the
signalling issues.

Example Icecast configuration:

.. code-block:: xml

    <mount>
      <mount-name>/mopidy</mount-name>
      <fallback-mount>/silence.mp3</fallback-mount>
      <fallback-override>1</fallback-override>
    </mount>

The ``silence.mp3`` file needs to be placed in the directory defined by
``<webroot>...</webroot>``.
