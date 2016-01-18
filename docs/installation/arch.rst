.. _arch-install:

**********************************
Arch Linux: Install from community
**********************************

If you are running Arch Linux, you can install Mopidy using the
`mopidy <https://www.archlinux.org/packages/community/any/mopidy/>`_ package found in ``community``.

#. To install Mopidy with all dependencies, you can use::

       pacman -S mopidy

   To upgrade Mopidy to future releases, just upgrade your system using::

       pacman -Syu

#. Finally, you need to set a couple of :doc:`config values </config>`, and
   then you're ready to :doc:`run Mopidy </running>` or run Mopidy as a
   :ref:`service <service>`.


Installing extensions
=====================

If you want to use any Mopidy extensions, like Spotify support or Last.fm
scrobbling, AUR has `packages for lots of Mopidy extensions
<https://aur.archlinux.org/packages/?K=mopidy>`_.

You can also install any Mopidy extension directly from PyPI with ``pip``. To
list all the extensions available from PyPI, run::

    pip search mopidy

Note that extensions installed from PyPI will only automatically install Python
dependencies. Please refer to the extension's documentation for information
about any other requirements needed for the extension to work properly.

For a full list of available Mopidy extensions, including those not installable
from AUR, see :ref:`ext`.
