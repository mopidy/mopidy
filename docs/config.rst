.. _config:

*************
Configuration
*************

Mopidy has a lot of config values you can tweak, but you only need to change a
few to get up and running. A complete :file:`~/.config/mopidy/mopidy.conf` may
be as simple as this:

.. code-block:: ini

    [mpd]
    hostname = ::

    [spotify]
    username = alice
    password = mysecret

Mopidy primarily reads config from the file
:file:`~/.config/mopidy/mopidy.conf`, where ``~`` means your *home directory*.
If your username is ``alice`` and you are running Linux, the config file should
probably be at :file:`/home/alice/.config/mopidy/mopidy.conf`. You can either
create the configuration file yourself, or run the ``mopidy`` command, and it
will create an empty config file for you and print what config values must be
set to successfully start Mopidy.

If running Mopidy as a service, the location of the config file and other
details documented here differs a bit. See :ref:`service` for details about
this.

When you have created the configuration file, open it in a text editor, and add
the config values you want to change.  If you want to keep the default for a
config value, you **should not** add it to the config file, but leave it out so
that when we change the default value in a future version, you won't have to
change your configuration accordingly.

To see what's the effective configuration for your Mopidy installation, you can
run::

    mopidy config

This will print your full effective config with passwords masked out so that
you safely can share the output with others for debugging.

You can find a description of all config values belonging to Mopidy's core
below, together with their default values. In addition, all :ref:`extensions
<ext>` got additional config values. The extension's config values and config
defaults are documented on the :ref:`extension pages <ext>`.


Default configuration
=====================

This is the default configuration for Mopidy itself. All extensions bring
additional configuration values with their own defaults.

.. literalinclude:: ../mopidy/config/default.conf
    :language: ini


Core config section
===================

.. confval:: core/cache_dir

    Path to base directory for storing cached data.

    Mopidy and extensions will use this path to cache data that can safely be
    thrown away.

    If your system is running from an SD card, it can help avoid wear and
    corruption of your SD card by pointing this config to another location. If
    you have enough RAM, a tmpfs might be a good choice.

    When running Mopidy as a regular user, this should usually be
    ``$XDG_CACHE_DIR/mopidy``, i.e. :file:`~/.cache/mopidy`.

    When running Mopidy as a system service, this should usually be
    :file:`/var/cache/mopidy`.

.. confval:: core/config_dir

    Path to base directory for config files.

    When running Mopidy as a regular user, this should usually be
    ``$XDG_CONFIG_DIR/mopidy``, i.e. :file:`~/.config/mopidy`.

    When running Mopidy as a system service, this should usually be
    :file:`/etc/mopidy`.

.. confval:: core/data_dir

    Path to base directory for persistent data files.

    Mopidy and extensions will use this path to store data that cannot be
    be thrown away and reproduced without some effort. Examples include
    Mopidy-Local's index of your media library and Mopidy-M3U's stored
    playlists.

    When running Mopidy as a regular user, this should usually be
    ``$XDG_DATA_DIR/mopidy``, i.e. :file:`~/.local/share/mopidy`.

    When running Mopidy as a system service, this should usually be
    :file:`/var/lib/mopidy`.

.. confval:: core/max_tracklist_length

    Max length of the tracklist. Defaults to 10000.

    The original MPD server only supports 10000 tracks in the tracklist. Some
    MPD clients will crash if this limit is exceeded.

.. confval:: core/restore_state

    When set to ``true``, Mopidy restores its last state when started.
    The restored state includes the tracklist, playback history,
    the playback state, the volume, and mute state.

    Default is ``false``.

.. _audio-config:

Audio configuration
===================

These are the available audio configurations. For specific use cases, see
:ref:`audio`.

.. confval:: audio/mixer

    Audio mixer to use.

    The default is ``software``, which does volume control inside Mopidy before
    the audio is sent to the audio output. This mixer does not affect the
    volume of any other audio playback on the system. It is the only mixer that
    will affect the audio volume if you're streaming the audio from Mopidy
    through Shoutcast.

    If you want to disable audio mixing set the value to ``none``.

    If you want to use a hardware mixer, you need to install a Mopidy extension
    which integrates with your sound subsystem. E.g. for ALSA, install
    `Mopidy-ALSAMixer <https://github.com/mopidy/mopidy-alsamixer>`_.

.. confval:: audio/mixer_volume

    Initial volume for the audio mixer.

    Expects an integer between 0 and 100.

    Setting the config value to blank leaves the audio mixer volume unchanged.
    For the software mixer blank means 100.

.. confval:: audio/output

    Audio output to use.

    Expects a GStreamer sink. Typical values are ``autoaudiosink``,
    ``alsasink``, ``osssink``, ``oss4sink``, ``pulsesink``, and ``shout2send``,
    and additional arguments specific to each sink. You can use the command
    ``gst-inspect-1.0`` to see what output properties can be set on the sink.
    For example: ``gst-inspect-1.0 shout2send``

.. confval:: audio/buffer_time

    Buffer size in milliseconds.

    Expects an integer above 0.

    Sets the buffer size of the GStreamer queue. If you experience buffering
    before track changes, it may help to increase this, possibly by at least a
    few seconds. The default is letting GStreamer decide the size, which at the
    time of this writing is 1000.


Logging configuration
=====================

.. confval:: logging/color

    Whether or not to colorize the console log based on log level. Defaults to
    ``true``.

.. confval:: logging/console_format

    The log format used for informational logging.

    See `the Python logging docs`_ for details on the format.

.. confval:: logging/debug_format

    The log format used for debug logging.

    See `the Python logging docs`_ for details on the format.

.. confval:: logging/debug_file

    The file to dump debug log data to when Mopidy is run with the
    :option:`mopidy --save-debug-log` option.

.. confval:: logging/config_file

    Config file that overrides all logging config values, see `the Python
    logging docs`_ for details.

.. confval:: loglevels/*

    The ``loglevels`` config section can be used to change the log level for
    specific parts of Mopidy during development or debugging. Each key in the
    config section should match the name of a logger. The value is the log
    level to use for that logger, one of ``debug``, ``info``, ``warning``,
    ``error``, or ``critical``.

.. confval:: logcolors/*

    The ``logcolors`` config section can be used to change the log color for
    specific parts of Mopidy during development or debugging. Each key in the
    config section should match the name of a logger. The value is the color
    to use for that logger, one of ``black``, ``red``, ``green``, ``yellow``,
    ``blue``, ``magenta``, ``cyan`` or ``white``.

.. _the Python logging docs: https://docs.python.org/2/library/logging.config.html


.. _proxy-config:

Proxy configuration
===================

Not all parts of Mopidy or all Mopidy extensions respect the proxy
server configuration when connecting to the Internet. Currently, this is at
least used when Mopidy's audio subsystem reads media directly from the network,
like when listening to Internet radio streams, and by the Mopidy-Spotify
extension. With time, we hope that more of the Mopidy ecosystem will respect
these configurations to help users on locked down networks.

.. confval:: proxy/scheme

    URI scheme for the proxy server. Typically ``http``, ``https``, ``socks4``,
    or ``socks5``.

.. confval:: proxy/hostname

    Hostname of the proxy server.

.. confval:: proxy/port

    Port number of the proxy server.

.. confval:: proxy/username

    Username for the proxy server, if needed.

.. confval:: proxy/password

    Password for the proxy server, if needed.


Extension configuration
=======================

Each installed Mopidy extension adds its own configuration section with one or
more config values that you may want to tweak. For the available config
values, please refer to the docs for each extension. Most, if not all, can be
found at :ref:`ext`.

Mopidy extensions are enabled by default when they are installed. If you want
to disable an extension without uninstalling it, all extensions support the
``enabled`` config value even if it isn't explicitly documented by all
extensions. If the ``enabled`` config value is set to ``false`` the extension
will not be started. For example, to disable the Spotify extension, add the
following to your ``mopidy.conf``::

    [spotify]
    enabled = false


Adding new configuration values
===============================

Mopidy's config validator will validate all of its own config sections and the
config sections belonging to any installed extension. It will raise an error if
you add any config values in your config file that Mopidy doesn't know about.
This may sound obnoxious, but it helps us detect typos in your config, and to
warn about deprecated config values that should be removed or updated.

If you're extending Mopidy, and want to use Mopidy's configuration
system, you can add new sections to the config without triggering the config
validator. We recommend that you choose a good and unique name for the config
section so that multiple extensions to Mopidy can be used at the same time
without any danger of naming collisions.
