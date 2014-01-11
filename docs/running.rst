**************
Running Mopidy
**************

To start Mopidy, simply open a terminal and run::

    mopidy

For a complete reference to the Mopidy commands and their command line options,
see :ref:`mopidy-cmd`.

When Mopidy says ``MPD server running at [127.0.0.1]:6600`` it's ready to
accept connections by any MPD client. Check out our non-exhaustive
:doc:`/clients/mpd` list to find recommended clients.


Stopping Mopidy
===============

To stop Mopidy, press ``CTRL+C`` in the terminal where you started Mopidy.

Mopidy will also shut down properly if you send it the TERM signal, e.g. by
using ``pkill``::

    pkill mopidy


Init scripts
============

- The ``mopidy`` package at `apt.mopidy.com <http://apt.mopidy.com/>`__ comes
  with an `sysvinit init script
  <https://github.com/mopidy/mopidy/blob/debian/debian/mopidy.init>`_.

- The ``mopidy`` package in `Arch Linux AUR
  <https://aur.archlinux.org/packages/mopidy>`__ comes with a systemd init
  script.

- A blog post by Benjamin Guillet explains how to `Daemonize Mopidy and Launch
  It at Login on OS X
  <http://www.benjaminguillet.com/blog/2013/08/16/launch-mopidy-at-login-on-os-x/>`_.

- Issue :issue:`266` contains a bunch of init scripts for Mopidy, including
  Upstart init scripts.
