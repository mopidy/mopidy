.. _audio:

*********************
Advanced audio setups
*********************

Mopidy has very few :ref:`audio configs <audio-config>`, but the ones we
have are very powerful because they let you modify the GStreamer audio pipeline
directly. Here we describe some use cases that can be solved with the audio
configs and GStreamer.


.. _custom-sink:

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


.. _streaming:

Streaming through Icecast
=========================

If you want to play the audio on another computer than the one running Mopidy,
you can stream the audio from Mopidy through an Icecast audio streaming server.
Multiple media players can then be connected to the streaming server
simultaneously. To use the Icecast output, do the following:

#. Install, configure and start the Icecast server. It can be found in the
   ``icecast2`` package in Debian/Ubuntu.

#. Set the :confval:`audio/output` config value to encode the output audio to
   MP3 (``lamemp3enc``) or Ogg Vorbis (``audioresample ! audioconvert !
   vorbisenc ! oggmux``) and send it to Icecast (``shout2send``).

   You might also need to change the ``shout2send`` default settings, run
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


Known issues
------------

- **Changing track:** As of Mopidy 1.2 we support gapless playback, and the
  stream does no longer end when changing from one track to another.

- **Previous/next:** The stream ends on previous and next. See :issue:`1306`
  for details. This can be worked around using a fallback stream, as described
  below.

- **Pause:** Pausing playback stops the stream. This is probably not something
  we're going to fix. This can be worked around using a fallback stream, as
  described below.

- **Metadata:** Track metadata is mostly missing from the stream. For Spotify,
  fixing :issue:`1357` should help. The general issue for other extensions is
  :issue:`866`.


Fallback stream
---------------

By using a *fallback stream* playing silence, you can somewhat mitigate the
known issues above.

Example Icecast configuration:

.. code-block:: xml

    <mount>
      <mount-name>/mopidy</mount-name>
      <fallback-mount>/silence.mp3</fallback-mount>
      <fallback-override>1</fallback-override>
    </mount>

You can easily find MP3 files with just silence by searching the web. The
``silence.mp3`` file needs to be placed in the directory defined by
``<webroot>...</webroot>`` in the Icecast configuration.
