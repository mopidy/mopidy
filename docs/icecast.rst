.. _icecast:

*******
Icecast
*******

If you want to play the audio on another computer than the one running Mopidy,
you can stream the audio from Mopidy through an Icecast audio streaming server.
Multiple media players can then be connected to the streaming server
simultaneously. To use the Icecast output, do the following:

.. warning::

    The last known working version of libshout3 is v2.4.1, this is the version
    available in Debian Buster. Newer versions of this library, such as those
    found in Ubuntu 20.04 and Debian Bullseye are bugged and render GStreamer's
    shout2send sink `broken
    <https://gitlab.freedesktop.org/gstreamer/gst-plugins-good/-/issues/848>`_
    and unusable. You cannot stream from Mopidy via Icecast with the below
    method when using Ubuntu 20.04 or Debian Bullseye. Consider `Snapcast
    <https://github.com/badaix/snapcast>`_ as an alternative solution.

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
       output = lamemp3enc ! shout2send async=false mount=mopidy ip=127.0.0.1 port=8000 password=hackme

   Example for Ogg Vorbis streaming:

   .. code-block:: ini

       [audio]
       output = audioresample ! audioconvert ! vorbisenc ! oggmux ! shout2send async=false mount=mopidy ip=127.0.0.1 port=8000 password=hackme

   Example for MP3 streaming and local audio (multiple outputs):

   .. code-block:: ini

       [audio]
       output = tee name=t ! queue ! audioresample ! autoaudiosink t. ! queue ! lamemp3enc ! shout2send async=false mount=mopidy ip=127.0.0.1 port=8000 password=hackme

Other advanced setups are also possible for outputs. Basically, anything you
can use with the ``gst-launch-1.0`` command can be plugged into
:confval:`audio/output`.


Known issues
============

- **Changing track:** As of Mopidy 1.2 we support gapless playback, and the
  stream does no longer end when changing from one track to another.

- **Previous/next:** The stream ends on previous and next. See :issue:`1306`
  for details. This can be worked around using a fallback stream, as described
  below.

- **Pause:** Pausing playback stops the stream. This is probably not something
  we're going to fix. This can be worked around using a fallback stream, as
  described below.

- **Metadata:** Track metadata might be missing from the stream. For Spotify,
  this should mostly work as of Mopidy 2.0.1. For other extensions,
  :issue:`866` is the tracking issue.


Fallback stream
===============

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
