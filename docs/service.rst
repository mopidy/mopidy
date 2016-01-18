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

All configuration is in :file:`/etc/mopidy`, not in your user's home directory.

The main configuration file is :file:`/etc/mopidy/mopidy.conf`.  If there are
more than one configuration file, this is the configuration file with the
highest priority, so it can override configs from all other config files.
Thus, you can do all your changes in this file.


mopidy user
===========

The init script runs Mopidy as the ``mopidy`` user, which is automatically
created when you install the Mopidy package. The ``mopidy`` user will need read
access to any local music you want Mopidy to play.


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
