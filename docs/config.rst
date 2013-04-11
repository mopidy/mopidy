*************
Configuration
*************

Mopidy has quite a few config values to tweak. Luckily, you only need to change
a few, and stay ignorant of the rest. Below you can find guides for typical
configuration changes you may want to do, and a listing of the available config
values.


Changing configuration
======================

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


.. _music-from-spotify:

Music from Spotify
==================

If you are using the Spotify backend, which is the default, enter your Spotify
Premium account's username and password into the file, like this:

.. code-block:: ini

    [spotify]
    username = myusername
    password = mysecret

This will only work if you have the Spotify Premium subscription. Spotify
Unlimited will not work.


.. _music-from-local-storage:

Music from local storage
========================

If you want use Mopidy to play music you have locally at your machine instead
of or in addition to using Spotify, you need to review and maybe change some of
the local backend config values. See :ref:`ext-local`, for a complete list.
Then you need to generate a tag cache for your local music...


.. _generating-a-tag-cache:

Generating a tag cache
----------------------

The program :command:`mopidy-scan` will scan the path set in the
:confval:`local/media_dir` config value for any media files and build a MPD
compatible ``tag_cache``.

To make a ``tag_cache`` of your local music available for Mopidy:

#. Ensure that the :confval:`local/media_dir` config value points to where your
   music is located. Check the current setting by running::

    mopidy --show-config

#. Scan your media library. The command outputs the ``tag_cache`` to
   standard output, which means that you will need to redirect the output to a
   file yourself::

    mopidy-scan > tag_cache

#. Move the ``tag_cache`` file to the location
   set in the :confval:`local/tag_cache_file` config value, or change the
   config value to point to where your ``tag_cache`` file is.

#. Start Mopidy, find the music library in a client, and play some local music!


.. _use-mpd-on-a-network:

Connecting from other machines on the network
=============================================

As a secure default, Mopidy only accepts connections from ``localhost``. If you
want to open it for connections from other machines on your network, see
the documentation for the :confval:`mpd/hostname` config value.

If you open up Mopidy for your local network, you should consider turning on
MPD password authentication by setting the :confval:`mpd/password` config value
to the password you want to use.  If the password is set, Mopidy will require
MPD clients to provide the password before they can do anything else. Mopidy
only supports a single password, and do not support different permission
schemes like the original MPD server.


Scrobbling tracks to Last.fm
============================

If you want to submit the tracks you are playing to your `Last.fm
<http://www.last.fm/>`_ profile, make sure you've installed the dependencies
found at :mod:`mopidy.frontends.scrobbler` and add the following to your
settings file:

.. code-block:: ini

    [scrobbler]
    username = myusername
    password = mysecret


.. _install-desktop-file:

Controlling Mopidy through the Ubuntu Sound Menu
================================================

If you are running Ubuntu and installed Mopidy using the Debian package from
APT you should be able to control Mopidy through the `Ubuntu Sound Menu
<https://wiki.ubuntu.com/SoundMenu>`_ without any changes.

If you installed Mopidy in any other way and want to control Mopidy through the
Ubuntu Sound Menu, you must install the ``mopidy.desktop`` file which can be
found in the ``data/`` dir of the Mopidy source into the
``/usr/share/applications`` dir by hand::

    cd /path/to/mopidy/source
    sudo cp data/mopidy.desktop /usr/share/applications/

After you have installed the file, start Mopidy in any way, and Mopidy should
appear in the Ubuntu Sound Menu. When you quit Mopidy, it will still be listed
in the Ubuntu Sound Menu, and may be restarted by selecting it there.

The Ubuntu Sound Menu interacts with Mopidy's MPRIS frontend,
:mod:`mopidy.frontends.mpris`. The MPRIS frontend supports the minimum
requirements of the `MPRIS specification <http://www.mpris.org/>`_. The
``TrackList`` interface of the spec is not supported.


Using a custom audio sink
=========================

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


Streaming audio through a SHOUTcast/Icecast server
==================================================

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


Custom configuration values
===========================

Mopidy's settings validator will stop you from defining any config values in
your settings file that Mopidy doesn't know about. This may sound obnoxious,
but it helps us detect typos in your settings, and deprecated settings that
should be removed or updated.

If you're extending Mopidy, and want to use Mopidy's configuration
system, you can add new sections to the config without triggering the config
validator. We recommend that you choose a good and unique name for the config
section so that multiple extensions to Mopidy can be used at the same time
without any danger of naming collisions.


Available settings
==================

.. note:: TODO: Document config values of the new config system
