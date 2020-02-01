.. _fedora-install:

******
Fedora
******

If you run Fedora 30 or newer you can install `mopidy
<https://src.fedoraproject.org/rpms/mopidy>`_ and `mopidy-mpd
<https://src.fedoraproject.org/rpms/mopidy-mpd>`_ from the standard Fedora
repositories.  `mopidy-spotify
<https://admin.rpmfusion.org/pkgdb/package/nonfree/mopidy-spotify/>`_
is available from RPMFusion.


Install Mopidy
==============

#. Install Mopidy and all dependencies::

       sudo dnf install mopidy

   This will automatically install Mopidy-MPD as a weak dependency as well.

#. Some extensions are packaged in RPMFusion.  To `install this repository
   <https://rpmfusion.org/Configuration>`_, run::

       sudo dnf install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm

#. Now, you're ready to :ref:`run Mopidy <running>`.


Installing extensions
=====================

If you want to use any Mopidy extensions, you need to install additional
packages.  Note that as of Feburary 2020, only Mopidy-MPD (automatically
installed) and Mopidy-Spotify (RPMFusion-nonfree) are packaged.

To install ``mopidy-spotify`` from RPMFusion-nonfree, simply run::

   sudo dnf install mopidy-spotify

If you cannot find the extension you want in the repositories, you can install
it from PyPI using ``pip`` instead.  Even if Mopidy itself is installed from
DNF it will correctly detect and use extensions from PyPI installed globally on
your system using::

   sudo python3 -m pip install ...

For a comprehensive index of available Mopidy extensions, including those not
installable from DNF, see the `Mopidy extension registry
<https://mopidy.com/ext/>`_.
