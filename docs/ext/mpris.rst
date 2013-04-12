.. _ext-mpris:

************
Mopidy-MPRIS
************

This extension lets you control Mopidy through the Media Player Remote
Interfacing Specification (`MPRIS <http://www.mpris.org/>`_) D-Bus interface.

An example of an MPRIS client is the :ref:`ubuntu-sound-menu`.


Dependencies
============

- D-Bus Python bindings. The package is named ``python-dbus`` in
  Ubuntu/Debian.

- ``libindicate`` Python bindings is needed to expose Mopidy in e.g. the
  Ubuntu Sound Menu. The package is named ``python-indicate`` in
  Ubuntu/Debian.

- An ``.desktop`` file for Mopidy installed at the path set in the
  :confval:`mpris/desktop_file` config value. See usage section below for
  details.


Default configuration
=====================

.. literalinclude:: ../../mopidy/frontends/mpris/ext.conf
    :language: ini


Configuration values
====================

.. confval:: mpris/enabled

    If the MPRIS extension should be enabled or not.

.. confval:: mpris/desktop_file

    Location of the Mopidy ``.desktop`` file.


Usage
=====

The extension is enabled by default if all dependencies are available.


Controlling Mopidy through the Ubuntu Sound Menu
------------------------------------------------

If you are running Ubuntu and installed Mopidy using the Debian package from
APT you should be able to control Mopidy through the :ref:`ubuntu-sound-menu`
without any changes.

If you installed Mopidy in any other way and want to control Mopidy through the
Ubuntu Sound Menu, you must install the ``mopidy.desktop`` file which can be
found in the ``data/`` dir of the Mopidy source repo into the
``/usr/share/applications`` dir by hand::

    cd /path/to/mopidy/source
    sudo cp data/mopidy.desktop /usr/share/applications/

If the correct path to the installed ``mopidy.desktop`` file on your system
isn't ``/usr/share/applications/mopidy.conf``, you'll need to set the
:confval:`mpris/desktop_file` config value.

After you have installed the file, start Mopidy in any way, and Mopidy should
appear in the Ubuntu Sound Menu. When you quit Mopidy, it will still be listed
in the Ubuntu Sound Menu, and may be restarted by selecting it there.

The Ubuntu Sound Menu interacts with Mopidy's MPRIS frontend. The MPRIS
frontend supports the minimum requirements of the `MPRIS specification
<http://www.mpris.org/>`_. The ``TrackList`` interface of the spec is not
supported.


Testing the MPRIS API directly
------------------------------

To use the MPRIS API directly, start Mopidy, and then run the following in a
Python shell::

    import dbus
    bus = dbus.SessionBus()
    player = bus.get_object('org.mpris.MediaPlayer2.mopidy',
        '/org/mpris/MediaPlayer2')

Now you can control Mopidy through the player object. Examples:

- To get some properties from Mopidy, run::

    props = player.GetAll('org.mpris.MediaPlayer2',
        dbus_interface='org.freedesktop.DBus.Properties')

- To quit Mopidy through D-Bus, run::

    player.Quit(dbus_interface='org.mpris.MediaPlayer2')

For details on the API, please refer to the `MPRIS specification
<http://www.mpris.org/>`_.
