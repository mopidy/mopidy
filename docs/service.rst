.. _service:

********************
Running as a service
********************

If you want to run Mopidy as a service using either an init script or a systemd
service, there's a few differences from running Mopidy as your own user you'll
want to know about. The following applies to Debian, Ubuntu, Raspbian, and
Arch. Hopefully, other distributions packaging Mopidy will make sure this works
the same way on their distribution.


Configuration
=============

All configuration is in :file:`/etc/mopidy/mopidy.conf`, not in your user's
home directory.


mopidy user
===========

The Mopidy service runs as the ``mopidy`` user, which is automatically created
when you install the Mopidy package. The ``mopidy`` user will need read access
to any local music you want Mopidy to play.


Subcommands
===========

To run Mopidy subcommands with the same user and config files as the service
uses, you can use ``sudo mopidyctl <subcommand>``. In other words, where you'll
usually run::

    mopidy config

You should instead run the following to inspect the service's configuration::

    sudo mopidyctl config

The same applies to scanning your local music collection. Where you'll normally
run::

    mopidy local scan

You should instead run::

    sudo mopidyctl local scan


Service management with systemd
===============================

On modern systems using systemd you can enable the Mopidy service by running::

    sudo systemctl enable mopidy

This will make Mopidy start when the system boots.

Mopidy is started, stopped, and restarted just like any other systemd service::

    sudo systemctl start mopidy
    sudo systemctl stop mopidy
    sudo systemctl restart mopidy

You can check if Mopidy is currently running as a service by running::

    sudo systemctl status mopidy


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


Service on OS X
===============

If you're installing Mopidy on OS X, see :ref:`osx-service`.


Configure PulseAudio
====================

When using PulseAudio, you will typically have a PulseAudio server run by your
main user. Since Mopidy is running as its own user, it can't access this server
directly. Running PulseAudio as a system-wide daemon is discouraged by upstream
(see `here
<http://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/WhatIsWrongWithSystemWide/>`_
for details). Rather you can configure PulseAudio and Mopidy so Mopidy sends
the sound to the PulseAudio server already running as your main user.

First, configure PulseAudio to accept sound over TCP from localhost by
uncommenting or adding the TCP module to :file:`/etc/pulse/default.pa` or
:file:`$XDG_CONFIG_HOME/pulse/default.pa` (typically
:file:`~/.config/pulse/default.pa`)::

    ### Network access (may be configured with paprefs, so leave this commented
    ### here if you plan to use paprefs)
    #load-module module-esound-protocol-tcp
    load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1
    #load-module module-zeroconf-publish

Next, configure Mopidy to use this PulseAudio server::

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
