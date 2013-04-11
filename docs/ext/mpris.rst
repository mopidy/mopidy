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
  :confval:`mpris/desktop_file` config value. See :ref:`install-desktop-file`
  for details.


Configuration values
====================

.. confval:: mpris/enabled

    If the MPRIS extension should be enabled or not.

.. confval:: mpris/desktop_file

    Location of the Mopidy ``.desktop`` file.


Default configuration
=====================

.. literalinclude:: ../../mopidy/frontends/mpris/ext.conf
    :language: ini


Usage
=====

The extension is enabled by default if all dependencies are available.


Testing the MPRIS API
=====================

To test, start Mopidy, and then run the following in a Python shell::

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
