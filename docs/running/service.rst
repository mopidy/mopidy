.. _service:

********************
Running as a service
********************

By running Mopidy as a system service, using e.g. systemd, it will
automatically be started when your system starts. This is the preferred
way to run Mopidy for most users.

The exact way Mopidy behaves when it runs as a service might vary depending
on your operating system or distribution.
The following applies to Debian, Ubuntu, Raspbian, and Arch Linux.
Hopefully, other distributions packaging Mopidy will make sure this works
the same way on their distribution.


Configuration
=============

When running Mopidy as a system service, configuration is read from
:file:`/etc/mopidy/mopidy.conf`,
and not from :file:`~/.config/mopidy/mopidy.conf`.

To print Mopidy's *effective* configuration, i.e. the combination of defaults,
your configuration file, and any command line options, you can run::

    sudo mopidyctl config

This will print your full effective config with passwords masked out so that
you safely can share the output with others for debugging.


Service user
============

The Mopidy system service runs as the ``mopidy`` user, which is automatically
created when you install the Mopidy package. The ``mopidy`` user will need
read access to any local music you want Mopidy to play.

.. note::
    If you're packaging Mopidy for a new distribution, make sure to
    automatically create the ``mopidy`` user when the package is installed.


Subcommands
===========

To run Mopidy subcommands with the same user and config files as the service
uses, you should use ``sudo mopidyctl <subcommand>``.

In other words, where someone running Mopidy manually in a terminal would run::

    mopidy <subcommand>

You should instead run the following::

    sudo mopidyctl <subcommand>


.. note::
    If you're packaging Mopidy for a new distribution, you'll find the
    :command:`mopidyctl` command in the :file:`extra/mopidyctl/` directory in
    the Mopidy Git repository.


Service management with systemd
===============================

On systems using systemd you can enable the Mopidy service by running::

    sudo systemctl enable mopidy

This will make Mopidy automatically start when the system starts.

Mopidy is started, stopped, and restarted just like any other systemd service::

    sudo systemctl start mopidy
    sudo systemctl stop mopidy
    sudo systemctl restart mopidy

You can check if Mopidy is currently running as a service by running::

    sudo systemctl status mopidy

You can use ``journalctl`` to view Mopidy's log,
including important error messages::

    sudo journalctl -u mopidy

``journalctl`` has many useful options,
including ``-f/--follow`` and ``-e/--pager-end``,
so please check out ``journalctl --help`` and ``man journalctl``.


Service management on Debian
============================

On Debian systems (both those using systemd and not) you can enable the Mopidy
service by running::

    sudo dpkg-reconfigure mopidy

Mopidy can be started, stopped, and restarted using the ``service`` command::

    sudo service mopidy start
    sudo service mopidy stop
    sudo service mopidy restart

You can check if Mopidy is currently running as a service by running::

    sudo service mopidy status


Service on macOS
================

On macOS, you can use ``launchctl`` to start Mopidy automatically at login
as your own user.

With Homebrew
-------------

If you installed Mopidy from Homebrew, simply run ``brew info mopidy`` and
follow the instructions in the "Caveats" section::

    $ brew info mopidy
    ...
    ==> Caveats
    To have launchd start mopidy/mopidy/mopidy now and restart at login:
        brew services start mopidy/mopidy/mopidy
    Or, if you don't want/need a background service, you can just run:
        mopidy

See ``brew services --help`` for how to start/restart/stop the service.

Without Homebrew
----------------

If you happen to be on macOS, but didn't install Mopidy with Homebrew, you can
get the same effect by adding the file
:file:`~/Library/LaunchAgents/mopidy.plist` with the following contents:

.. code:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
      <key>Label</key>
      <string>mopidy</string>
      <key>ProgramArguments</key>
      <array>
        <string>/usr/local/bin/mopidy</string>
      </array>
      <key>RunAtLoad</key>
      <true/>
      <key>KeepAlive</key>
      <true/>
    </dict>
    </plist>

You might need to adjust the path to the ``mopidy`` executable,
``/usr/local/bin/mopidy``, to match your system.

Then, to start Mopidy with ``launchctl`` right away::

    launchctl load ~/Library/LaunchAgents/mopidy.plist


System service and PulseAudio
=============================

When using PulseAudio, you will typically have a PulseAudio server run by your
main user. Since Mopidy as a system service is running as its own user,
it can't access your PulseAudio server directly.
Running PulseAudio as a system-wide daemon is discouraged by upstream
(see `here
<https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/WhatIsWrongWithSystemWide/>`_
for details). Rather you can configure PulseAudio and Mopidy so that Mopidy
sends the audio to the PulseAudio server already running as your main user.

First, configure PulseAudio to accept sound over TCP from localhost by
uncommenting or adding the TCP module to :file:`/etc/pulse/default.pa` or
:file:`$XDG_CONFIG_HOME/pulse/default.pa` (typically
:file:`~/.config/pulse/default.pa`)::

    ### Network access (may be configured with paprefs, so leave this commented
    ### here if you plan to use paprefs)
    #load-module module-esound-protocol-tcp
    load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1
    #load-module module-zeroconf-publish

Next, configure Mopidy to use this PulseAudio server:

.. code-block:: ini

    [audio]
    output = pulsesink server=127.0.0.1

After this, restart both PulseAudio and Mopidy::

    pulseaudio --kill
    start-pulseaudio-x11
    sudo systemctl restart mopidy

If you are not running any X server, run ``pulseaudio --start`` instead of
``start-pulseaudio-x11``.

If you don't want to hard code the output in your Mopidy config, you can
instead of adding any config to Mopidy add this to
:file:`~mopidy/.pulse/client.conf`::

    default-server=127.0.0.1
