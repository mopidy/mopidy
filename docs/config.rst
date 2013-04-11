*************
Configuration
*************

Mopidy has quite a few config values to tweak. Luckily, you only need to change
a few, and stay ignorant of the rest. Below you can find guides for typical
configuration changes you may want to do, and a listing of the available config
values.

Mopidy primarily reads config from the file ``~/.config/mopidy/mopidy.conf``,
where ``~`` means your *home directory*. If your username is ``alice`` and you
are running Linux, the settings file should probably be at
``/home/alice/.config/mopidy/mopidy.conf``.

You can either create the configuration file yourself, or run the ``mopidy``
command, and it will create an empty settings file for you.

When you have created the configuration file, open it in a text editor, and add
settings you want to change. If you want to keep the default value for a
setting, you should *not* redefine it in your own settings file.

A complete ``~/.config/mopidy/mopidy.conf`` may look as simple as this:

.. code-block:: ini

    [mpd]
    hostname = ::

    [spotify]
    username = alice
    password = mysecret


Core configuration values
=========================

TODO


Default core configuration
==========================

TODO


Advanced configurations
=======================

Custom audio sink
-----------------

If you have successfully installed GStreamer, and then run the ``gst-inspect``
or ``gst-inspect-0.10`` command, you should see a long listing of installed
plugins, ending in a summary line::

    $ gst-inspect-0.10
    ... long list of installed plugins ...
    Total count: 254 plugins (1 blacklist entry not shown), 1156 features

Next, you should be able to produce a audible tone by running::

    gst-launch-0.10 audiotestsrc ! audioresample ! autoaudiosink

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

Again, this is the equivalent of the following ``gst-inspect`` command, so make
this work first::

    gst-launch-0.10 audiotestsrc ! audioresample ! oss4sink


Streaming through SHOUTcast/Icecast
-----------------------------------

If you want to play the audio on another computer than the one running Mopidy,
you can stream the audio from Mopidy through an SHOUTcast or Icecast audio
streaming server. Multiple media players can then be connected to the streaming
server simultaneously. To use the SHOUTcast output, do the following:

#. Install, configure and start the Icecast server. It can be found in the
   ``icecast2`` package in Debian/Ubuntu.

#. Set the :confval:`audio/output` config value to ``lame ! shout2send``. An
   Ogg Vorbis encoder could be used instead of the lame MP3 encoder.

#. You might also need to change the ``shout2send`` default settings, run
   ``gst-inspect-0.10 shout2send`` to see the available settings. Most likely
   you want to change ``ip``, ``username``, ``password``, and ``mount``. For
   example, to set the username and password, use:

   .. code-block:: ini

       [audio]
       output = lame ! shout2send username="alice" password="secret"

Other advanced setups are also possible for outputs. Basically, anything you
can use with the ``gst-launch-0.10`` command can be plugged into
:confval:`audio/output`.


New configuration values
------------------------

Mopidy's settings validator will stop you from defining any config values in
your settings file that Mopidy doesn't know about. This may sound obnoxious,
but it helps us detect typos in your settings, and deprecated settings that
should be removed or updated.

If you're extending Mopidy, and want to use Mopidy's configuration
system, you can add new sections to the config without triggering the config
validator. We recommend that you choose a good and unique name for the config
section so that multiple extensions to Mopidy can be used at the same time
without any danger of naming collisions.
