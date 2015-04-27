.. _debian-install:

******************************************
Debian/Ubuntu: Install from apt.mopidy.com
******************************************

If you run a Debian based Linux distribution, like Ubuntu, the easiest way to
install Mopidy is from the `Mopidy APT archive <https://apt.mopidy.com/>`_.
When installing from the APT archive, you will automatically get updates to
Mopidy in the same way as you get updates to the rest of your system.

If you're on a Raspberry Pi running Debian or Raspbian, the following
instructions should work for you as well. If you're setting up a Raspberry Pi
from scratch, we have a guide for installing Debian/Raspbian and Mopidy. See
:ref:`raspberrypi-installation`.

.. note::

   The packages should work with:

   - Debian stable ("jessie") and testing ("stretch"),
   - Raspbian stable ("jessie") and testing ("stretch"),
   - Ubuntu 14.04 LTS and later.

   Some of the packages *do not* work with Ubuntu 12.04 LTS or Debian 7
   "wheezy".

   This is just what we currently support, not a promise to continue to
   support the same in the future. We *will* drop support for older
   distributions when supporting those stops us from moving forward with the
   project.

#. Add the archive's GPG key::

       wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -

#. Add the following to ``/etc/apt/sources.list``, or if you have the directory
   ``/etc/apt/sources.list.d/``, add it to a file called ``mopidy.list`` in
   that directory::

       # Mopidy APT archive
       deb http://apt.mopidy.com/ stable main contrib non-free
       deb-src http://apt.mopidy.com/ stable main contrib non-free

   For the lazy, you can simply run the following command to create
   ``/etc/apt/sources.list.d/mopidy.list``::

       sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/mopidy.list

   .. note::

       If you're still running Debian 7 "wheezy" or Raspbian "wheezy", you
       should edit :file:`/etc/apt/sources.list.d/mopidy.list` and replace
       "stable" with "wheezy". This will give you the latest set of packages
       that is compatible with Debian "wheezy".

#. Install Mopidy and all dependencies::

       sudo apt-get update
       sudo apt-get install mopidy

#. Before continuing, make sure you've read the :ref:`debian` section to learn
   about the differences between running Mopidy as a system service and
   manually as your own system user.

#. Finally, you need to set a couple of :doc:`config values </config>`, and then
   you're ready to :doc:`run Mopidy </running>`.

When a new release of Mopidy is out, and you can't wait for you system to
figure it out for itself, run the following to upgrade right away::

    sudo apt-get update
    sudo apt-get dist-upgrade


Installing extensions
=====================

If you want to use any Mopidy extensions, like Spotify support or Last.fm
scrobbling, you need to install additional packages.

To list all the extensions available from apt.mopidy.com, you can run::

    apt-cache search mopidy

To install one of the listed packages, e.g. ``mopidy-spotify``, simply run::

   sudo apt-get install mopidy-spotify

You can also install any Mopidy extension directly from PyPI with ``pip``. To
list all the extensions available from PyPI, run::

    pip search mopidy

Note that extensions installed from PyPI will only automatically install Python
dependencies. Please refer to the extension's documentation for information
about any other requirements needed for the extension to work properly.

For a full list of available Mopidy extensions, including those not
installable from apt.mopidy.com, see :ref:`ext`.


Missing extensions
==================

If you've installed a Mopidy extension with pip, restarted Mopidy, and Mopidy
doesn't find the extension, there's probably a simple explanation and solution.

Mopidy installed with APT can detect and use Mopidy extensions installed with
both APT and pip. APT installs Mopidy as :file:`/usr/bin/mopidy`.

Mopidy installed with pip can only detect Mopidy extensions installed with pip.
pip usually installs Mopidy as :file:`/usr/local/bin/mopidy`.

If you have Mopidy installed from both APT and pip, then the pip-installed
Mopidy will probably shadow the APT-installed Mopidy because
:file:`/usr/local/bin` usually has precedence over :file:`/usr/bin` in the
``PATH`` environment variable. To check if this is the case on your system, you
can use ``which`` to see what installation of Mopidy you use when you run
``mopidy`` in your shell::

    $ which mopidy
    /usr/local/bin/mopidy

If this is the case on your system, the recommended solution is to check that
you have Mopidy installed from APT too::

    $ /usr/bin/mopidy --version
    Mopidy 0.19.5

And then uninstall the pip-installed Mopidy::

    sudo pip uninstall mopidy

Depending on what shell you use, the shell may still try to use
:file:`/usr/local/bin/mopidy` even if it no longer exists. Check again with
``which mopidy`` what your shell believes is the right ``mopidy`` executable to
run. If the shell is still confused, you may need to restart it, or in the case
of zsh, run ``rehash`` to update the shell.

For more details on why this works this way, see :ref:`debian`.
