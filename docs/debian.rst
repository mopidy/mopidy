.. _debian:

***************
Debian packages
***************

The Mopidy Debian package, ``mopidy``, is available from `apt.mopidy.com
<http://apt.mopidy.com/>`__ as well as from Debian, Ubuntu and other
Debian-based Linux distributions.

Some extensions are also available from all of these sources, while others,
like Mopidy-Spotify and its dependencies, are only available from
apt.mopidy.com. This may either be temporary until the package is uploaded to
Debian and with time propagates to the other distributions. It may also be more
long term, like in the Mopidy-Spotify case where there is uncertainities around
licensing and distribution of non-free packages.


Installation
============

See :ref:`debian-install`.


Running as a system service
===========================

The Debian package comes with an init script. It starts Mopidy as a system
service running as the ``mopidy`` user. The user is created by the package.

The Debian package might ask if you want to run Mopidy as a system service. If
you don't get the question, your system is probably configured to ignore
questions at that priority level during installs, and defaults to not enabling
the Mopidy service.

If you didn't get the question or if you've changed your mind about whether or
not to run Mopidy as a system service, just run the following command to
reconfigure the package::

    sudo dpkg-reconfigure mopidy


Differences when running as a system service
============================================

If you want to run Mopidy using the init script, there's a few differences
from a regular Mopidy setup you'll want to know about.

- All configuration is in :file:`/etc/mopidy`, not in your user's home
  directory. The main configuration file is :file:`/etc/mopidy/mopidy.conf`.
  This is the configuration file with the highest priority, so it can override
  configs from all other config files. Thus, you can do all your changes in
  this file.

- The init script runs Mopidy as the ``mopidy`` user. The ``mopidy`` user will
  need read access to any local music you want Mopidy to play.

- To run Mopidy subcommands with the same user and config files as the init
  script uses, you can use ``sudo mopidyctl <subcommand>``. In other words,
  where you'll usually run::

      mopidy config

  You should instead run the following to inspect the system service's
  configuration::

      sudo mopidyctl config

  The same applies to scanning your local music collection. Where you'll
  normally run::

      mopidy local scan

  You should instead run::

      sudo mopidyctl local scan

- Mopidy is started, stopped, and restarted just like any other system
  service::

      sudo service mopidy start
      sudo service mopidy stop
      sudo service mopidy restart

- You can check if Mopidy is currently running as a system service by running::

      sudo service mopidy status
