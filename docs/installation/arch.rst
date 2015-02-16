.. _arch-install:

****************************
Arch Linux: Install from AUR
****************************

If you are running Arch Linux, you can install Mopidy using the
`mopidy <https://aur.archlinux.org/packages/mopidy/>`_ package found in AUR.

#. To install Mopidy with all dependencies, you can use
   for example `yaourt <https://wiki.archlinux.org/index.php/yaourt>`_::

       yaourt -S mopidy

   To upgrade Mopidy to future releases, just upgrade your system using::

       yaourt -Syu

#. Optional: If you want to use any Mopidy extensions, like Spotify support or
   Last.fm scrobbling, AUR also has `packages for several Mopidy extensions
   <https://aur.archlinux.org/packages/?K=mopidy>`_.

   For a full list of available Mopidy extensions, including those not
   installable from AUR, see :ref:`ext`.

#. Finally, you need to set a couple of :doc:`config values </config>`, and
   then you're ready to :doc:`run Mopidy </running>`.
